#!/usr/bin/env python

import binascii
import commands
import datetime as dt
import logging
import os
import re
import subprocess
import tarfile
import time
import xapian

from apprecommender.apt_cache import AptCache
from apprecommender.config import Config
from apprecommender.data import get_user_installed_pkgs
from apprecommender.data_classification import get_alternative_pkg
from apprecommender.main.app_recommender import AppRecommender
from apprecommender.main.ml_cross_validation import ml_cross_validation
from apprecommender.ml.data import MachineLearningData
from apprecommender.ml.pkg_time import PkgTime
from apprecommender.utils import print_progress_bar

LOG_PATH = os.path.expanduser('~/app_recommender_log')
SUFIX = dt.datetime.now().strftime('%Y%m%d%H%M')
LOG_PATH += SUFIX
ALL_INSTALLED_PKGS = LOG_PATH + '/all_pkgs.txt'
MANUAL_INSTALLED_PKGS_PATH = LOG_PATH + '/manual_installed_pkgs.txt'
PKGS_TIME_PATH = LOG_PATH + '/pkgs_time.txt'
HISTORY = LOG_PATH + '/user_history.txt'
PKGS_BINARY = LOG_PATH + '/pkgs_binary.txt'
RECOMMENDATION_PATH = LOG_PATH + '/{0}_recommendation.txt'
USER_PREFERENCES = LOG_PATH + '/user_preferences.txt'
POPCON_SUBMISSION = LOG_PATH + '/popcon-submission'
PC_INFORMATIONS = LOG_PATH + '/pc_informations.txt'
RECOMMENDATIONS_TIME = LOG_PATH + '/recommendations_time.txt'


PKGS_DEPENDENCIES = []

RE_MATCH = re.compile(r'^\d:\s([^\s]+)', re.MULTILINE)


def create_log_folder():
    print "Creating log folder"
    if not os.path.exists(LOG_PATH):
        os.mkdir(LOG_PATH, 0755)


def create_file(file_path):
    if not os.path.exists(file_path):
        with open(file_path, 'a'):
            os.utime(file_path, None)
        return True

    return False


def delete_file(file_path):
    if os.path.exists(file_path):
        os.remove(file_path)


def save_list(list_to_save, file_path):
    delete_file(file_path)
    create_file(file_path)

    with open(file_path, 'w') as text:
        for element in list_to_save:
            text.write(str(element) + '\n')


def rename_file(original_name, new_name):
    os.rename(original_name, new_name)


def get_submission_id(submission_header):

    fields = submission_header.split(' ')
    return fields[2][3:]


def create_popularity_contest_file():
    if os.path.exists('popularity-contest.conf'):
        return

    host_id = binascii.hexlify(os.urandom(16))

    with open('popularity-contest.conf', 'w') as text:
        text.write('MY_HOSTID="{0}"\n'.format(host_id))
        text.write('PARTICIPATE="no"\n')
        text.write('USEHTTP="no"\n')
        text.write('DAY="4"\n')


def collect_popcon_submission():
    print "Collecting popularity-contest submission"

    create_popularity_contest_file()

    popcon = subprocess.Popen('./popularity-contest',
                              shell=False, stdin=subprocess.PIPE,
                              stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE)

    popcon_output = popcon.stdout.read()

    popcon_parse = popcon_output.splitlines()
    submission_id = get_submission_id(popcon_parse[0])

    submission = [line for line in popcon_parse]

    save_list(submission, POPCON_SUBMISSION)

    file_name = LOG_PATH + "/" + submission_id + ".txt"
    rename_file(POPCON_SUBMISSION, file_name)


def collect_manual_installed_pkgs():
    print "Collecting manual installed pkgs"

    if create_file(MANUAL_INSTALLED_PKGS_PATH):
        packages = commands.getoutput('apt-mark showmanual')

        packages = [pkg for pkg in packages.splitlines()]

        save_list(packages, MANUAL_INSTALLED_PKGS_PATH)


def collect_all_user_pkgs():
    print "Collecting all user packages"

    if create_file(ALL_INSTALLED_PKGS):
        packages = get_user_installed_pkgs()
        save_list(packages, ALL_INSTALLED_PKGS)


def collect_pkgs_time():
    print "Collecting packages time"

    pkg_time = PkgTime()

    if create_file(PKGS_TIME_PATH):
        manual_pkgs = []
        with open(MANUAL_INSTALLED_PKGS_PATH, 'r') as text:
            manual_pkgs = [line.strip() for line in text]

        pkgs_time = pkg_time.get_packages_time(manual_pkgs)

        pkg_time.save_package_time(pkgs_time, PKGS_TIME_PATH)


def get_pkg_binary(pkg):
    stat_command = "which {0}".format(pkg)
    pkg_bin = commands.getoutput(stat_command.format(pkg))

    if pkg_bin:
        return pkg

    return get_alternative_pkg(pkg)


def get_pkgs_of_recommendation(strategy):
    app_recommender = AppRecommender()

    app_recommender.recommender.set_strategy(strategy)
    rec = app_recommender.make_recommendation(print_recommendation=False)

    pkgs = RE_MATCH.findall(rec.__str__())

    return pkgs


def collect_user_preferences():
    Config().num_recommendations = 6
    strategies = ['cb', 'cb_eset', 'cbtm', 'mlbva', 'mlbva_eset', 'mlbow',
                  'mlbow_eset']

    recommendations = {}
    recommendations_time = []

    print "Preparing recommendations..."

    len_strategies = len(strategies)
    for index, strategy in enumerate(strategies):
        first_time = int(round(time.time() * 1000))
        recommendations[strategy] = get_pkgs_of_recommendation(strategy)
        last_time = int(round(time.time() * 1000))
        recommendations_time.append("{0}: {1}".format(strategy,
                                                      last_time - first_time))

        print_progress_bar(index + 1, len_strategies)

    all_recommendations = set(sum(recommendations.values(), []))
    all_recommendations = sorted(list(all_recommendations))

    index = 0
    user_preferences = {}
    all_rec_len = len(all_recommendations)

    message = "\n\nPackage [{0}/{1}] - {2} \n"
    message += "Description: {3}\n\n"
    message += "Rank a package recommendation with 1-4\n"
    message += "1 - Bad\n"
    message += "2 - Redundant\n"
    message += "3 - Useful\n"
    message += "4 - Useful Surprise\n\n"
    message += "exit - Cancel collect data\n\n"
    message += "Rank: "

    message_error = "\nPlease use digits 1-4 to rank a package: "

    apt_cache = AptCache()
    for i in range(len(all_recommendations)):
        pkg = all_recommendations[i]
        pkg_description = apt_cache[pkg].versions[0].description

        rank = -1

        raw_message = message.format((index + 1), all_rec_len, pkg,
                                     pkg_description)

        clear_prints()
        print "\n\nCollecting user preferences"

        if i > 0:
            print "\n"

        for j in range(i):
            prev_pkg = all_recommendations[j]

            print(
                "[{0}/{1}] {2}, rank: {3}".format(j + 1, all_rec_len, prev_pkg,
                                                  user_preferences[prev_pkg]))

        while rank < 1 or rank > 4:
            try:
                rank = raw_input(raw_message)

                if rank == 'exit':
                    break

                rank = int(rank)
            except:
                rank = -2

            raw_message = message_error

        if rank == 'exit':
            exit(2)

        user_preferences[pkg] = rank
        index += 1

    preferences_list = ["{0}:{1}".format(package, user_preferences[package])
                        for package in all_recommendations]

    for rec_key, rec_value in recommendations.iteritems():
        save_list(rec_value, RECOMMENDATION_PATH.format(rec_key))

    save_list(preferences_list, USER_PREFERENCES)
    save_list(recommendations_time, RECOMMENDATIONS_TIME)


def get_uninstalled_dependencies():
    user_pkgs = []
    unistalled_pkgs = []

    user_pkgs = get_user_installed_pkgs()

    for pkg in PKGS_DEPENDENCIES:
        if pkg not in user_pkgs:
            unistalled_pkgs.append(pkg)

    return unistalled_pkgs


def check_dependencies():
    unistalled_pkgs = get_uninstalled_dependencies()
    unistalled_dependencies = ''

    if len(unistalled_pkgs) > 0:
        unistalled_dependencies = ''.join(str(pkg) + ' '
                                          for pkg in unistalled_pkgs)

    return unistalled_dependencies


def collect_pc_informations():
    print "Collecting PC informations"
    informations = []
    linux_kernel_version = commands.getoutput('uname -s -r')

    distribution_version = commands.getoutput('lsb_release -a')
    distribution_version = distribution_version.splitlines()

    processor = commands.getoutput("cat /proc/cpuinfo | grep 'model name'")
    processor = processor.splitlines()[0].split(':')[1].strip()
    processor = "Processor: {0}".format(processor)

    informations.append(linux_kernel_version)
    informations.extend(distribution_version)
    informations.append(processor)

    save_list(informations, PC_INFORMATIONS)


def collect_user_data():
    collect_pc_informations()
    collect_all_user_pkgs()
    collect_manual_installed_pkgs()
    collect_pkgs_time()
    collect_popcon_submission()


def initial_prints():
    experiment_agree = """
        Participate in this package survey?

        This survey has the objective to collect user feedback to allow the
        comparison between some new strategies for AppRecommender. This survey
        will them present a series of recommended packages that can
        be evaluates as follows:

        Bad:             A package that you would not install on your system.
        Redundant:       You already have a package that provides the same
                         functionality as the one being recommended.
        Useful:          A package that you may install on you system.
        Useful Surprise: A package that you would install on your system, but
                         the recommendatio also surprised you in a positive
                         way.

        This survey will also collect the result of some cross validation
        metrics generated for the AppRecommender strategies that use machine
        learning.

        Therefore, this survey will collect the following data:

        * A list of your evaluations for the recommended packages.
        * The result of the cross validation metrics for AppRecommender machine
          learning strategies.
        * The time in seconds that it took for each strategies to genarate its
          recommendations

        Once this process is over, a tar.gz file will be generated on your HOME
        dir. After that just send this file over to:

        lucas.moura128@gmail.com
        lucianopcbr@gmail.com
        terceiro@debian.org
        """
    print experiment_agree


def user_accept_collect_data():
    accept_message = "\nDo you want to participate on this survey ? [y, N]: "
    accept_input = raw_input(accept_message)

    return accept_input.lower() == 'y'


def clear_prints():
    print '\n' * 80
    os.system('clear')


def train_machine_learning():
    try:
        print "Training machine learning"

        os.system("cp {} {}".format(
            MachineLearningData.PKGS_CLASSIFICATIONS, LOG_PATH))
    except xapian.DatabaseOpeningError:
        print "\n\nPlease check if you prepared the AppRecommender data"
        print "Try to run the following commands:"
        print "  $ cd .."
        print "  $ sudo apprec --init\n"
        exit(1)
    except IOError:
        print "\n\nPlease run the train command before executing this script:"
        print "  $ sudo apprec --train\n"


def run_cross_validation():
    print "Collecting cross validations"

    strategies = ['mlbva', 'mlbva_eset', 'mlbow', 'mlbow_eset']
    len_strategies = len(strategies)

    for index, strategy in enumerate(strategies):
        ml_cross_validation(LOG_PATH, strategy)
        print_progress_bar(index + 1, len_strategies)


def make_tarfile(output_filename, source_dir):
    with tarfile.open(output_filename, "w:gz") as tar:
        tar.add(source_dir, arcname=os.path.basename(source_dir))


def main():
    logging.getLogger().disabled = True

    initial_prints()
    if not user_accept_collect_data():
        exit(1)

    create_log_folder()
    train_machine_learning()
    run_cross_validation()
    collect_user_preferences()

    make_tarfile(LOG_PATH + '.tar.gz', LOG_PATH)
    subprocess.call(['rm', '-rf', LOG_PATH])

    print "\n\nFinished: All files and recommendations were collected"
    print "Collect data folder: {0}.tar.gz\n".format(LOG_PATH)
    print "Please, send this file to either one of these emails:\n"
    print "lucas.moura128@gmail.com, lucianopcbr@gmail.com, terceiro@debian.org"  # noqa

if __name__ == '__main__':
    main()
