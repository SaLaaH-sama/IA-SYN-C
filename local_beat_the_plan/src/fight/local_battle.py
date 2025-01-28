
from argparse import ArgumentParser, RawTextHelpFormatter
from src.referee import logs
from src.referee.referee import Player
from os.path import splitext, basename
from itertools import count
import random

OUTPUT_DIRECTORY = './html/'
OUTPUT_FILENAME = 'results.json'


def local_battle(referee):
    """
     On the website where the players can submit their program and see the ranking, they can download an archive to
     run a local version of the game without submitting and waiting for the ranking results. This local version
     should contain a file calling this class (more exactly calling a class that calls this function).

     Contrary to the Championship function which run continuously many battles to rank
     the players who submit on the website, this class runs only one battle at a time and the user can manipulate some
     options (increase the timeouts, choose the adversaries, display logs on the terminal).

     This function is used
     - firstly to print a help message if the user run the file with the option -h
     - secondly to run exactly one battle of a given Referee. The players or AI of the battle are chosen by the user
     manually. The results of the battle are printed in a JSON file that can be seen using a local PHP server in the
     html folder of the archive. The results can also be printed on the terminal directly.
     - thirdly, run many battles at once. In this case, no log is printed. At the end, the game print some stats (for
     instance, for each player, the number of win/loss)

    :param referee:

    """

    # Parse input parameters

    parser = ArgumentParser(referee.get_name(),
                            description="""
Tool for testing bots for the game %s
Author:  %s

Should be run in a folder containing :
- an html folder
""" % (referee.get_name(), referee.get_author()),
                            epilog="""
EXAMPLE
=======
python3 %s.py ./localIAs/ai1.sync /home/.../myai.sync
runs a battle with the bots from the two selected files  

OUTPUT
======
If the -s option is given, print some statistics on the console. 
Otherwise, produce a json file and save it to the file ./html/results.json. 
The file contains the necessary information to display the battle. It can then be read 
using the PHP script ./html/index.php. 

To do so, you can use the php server software of your choice. On most of the linux 
distribution, the simplest way consists in using the php -S command:
> cd html
> php -S localhost:8888
> firefox index.php 
""" % referee.get_filename(),
                            formatter_class=RawTextHelpFormatter)

    parser.add_argument('-lo', '--log-output', action='store_true',
                        help='Any string printed by a player is logged and displayed on the console.')
    parser.add_argument('-li', '--log-input', action='store_true',
                        help='Any string sent by the game to a player is logged and displayed on the console.')
    parser.add_argument('-ld', '--log-debug', action='store_true',
                        help='Any string printed by a player to the standard error is logged and displayed on the '
                             'console (and tagged as debugging message).')
    parser.add_argument('-lr', '--log-results', action='store_true',
                        help='The scores of all the players are displayed after the battle.')
    parser.add_argument('-lg', '--log-game', action='store_true',
                        help='Any string printed by the game (errors messages, win or loss messages, ...) is logged '
                             'and displayed on the console.')
    parser.add_argument('-la', '--log-all', action='store_true',
                        help='Equivalent to -lo -li -ld -lr -lg')
    parser.add_argument('-tm1', '--first-timeout', type=int,
                        help='Replace the default value of the first timeout (%d) -- that is, the number of elementary '
                             'operations that can be performed before the first PRINT -- by the given value.'
                             % Player.FIRST_MAX_ELEMENTARY_OPERATIONS_TIMEOUT)
    parser.add_argument('-tm', '--timeout', type=int,
                        help='Replace the default value of the timeout (%d) -- that is, the number of elementary '
                             'operations that can be performed between two PRINT -- by the given value.'
                             % Player.MAX_ELEMENTARY_OPERATIONS_TIMEOUT)
    parser.add_argument('-se', '--seed', type=int,
                        help='Replace the random seed by the given value. The seeds of the scripts are unchanged, this '
                             'option only affect the seed of the referee.')
    # parser.add_argument('-db', '--debug', action='store_true',
    #                     help='Set the debug mode. In this mode, one can ')
    parser.add_argument('-s', '--stats', type=int, metavar='NB_BATTLES',
                        help='Instead of running one battle, displaying the logs and the results, the program runs '
                             'NB_BATTLES battles and display some stats at the end (frequency of each ranking, '
                             'average score, number of loss). Logging options are ignored if -s is given.')
    parser.add_argument('sync_files', nargs='+')
    args = parser.parse_args()

    # Set logs according to input parameters
    logs.LOG_OUTPUT = (args.log_output or args.log_all) and args.stats is None
    logs.LOG_INPUT = (args.log_input or args.log_all) and args.stats is None
    logs.LOG_DEBUG = (args.log_debug or args.log_all) and args.stats is None
    logs.LOG_RESULTS = (args.log_results or args.log_all) and args.stats is None
    logs.LOG_GAME = (args.log_game or args.log_all) and args.stats is None

    # Set timeouts according to input parameters
    if args.first_timeout is not None:
        Player.FIRST_MAX_ELEMENTARY_OPERATIONS_TIMEOUT = args.first_timeout
    if args.timeout is not None:
        Player.MAX_ELEMENTARY_OPERATIONS_TIMEOUT = args.timeout
    if args.seed is not None:
        random.seed(args.seed)

    # Check input files
    if len(args.sync_files) not in referee.allowed_number_of_players():
        print('Incorrect numbers of files. Allowed number of players:',
              ' '.join([str(x) for x in referee.allowed_number_of_players()]))
        return

    def get_name(filename):
        return splitext(basename(filename))[0]

    # Set scripts of players according to input files
    scripts = dict()
    for script in args.sync_files:
        script_name = get_name(script)
        name = script_name
        for i in count():
            if name in scripts:
                name = script_name + '_' + str(i + 2)
                continue
            break
        scripts[name] = script

    # Play according to input parameters
    if args.stats is None:
        referee.play(scripts)
        referee.write_results_to(OUTPUT_DIRECTORY + OUTPUT_FILENAME)
    else:
        # User asks for statistics
        nb_battles = args.stats
        scores = []
        names = list(scripts.keys())
        # Play all the battles
        for i in range(nb_battles):
            print('Run battle', i + 1, '/', nb_battles, end='\r')
            referee.play(scripts)
            scores_of_battle = []
            for name in names:
                player = referee.get_player_by_name(name)
                scores_of_battle.append(player.score if not player.has_lost else None)
            scores.append(scores_of_battle)

        for i, name in enumerate(names):
            # For each player

            # Count the number of times the player did not reach the end of the game
            nb_loss = sum(1 if scores_of_battle[i] is None else 0 for scores_of_battle in scores)

            # Count the average score of the player on the non-loss battles
            if nb_loss == len(scores):
                avg_score = 'N/A'
            else:
                avg_score = '%.3f' % (sum(scores_of_battle[i] for scores_of_battle in scores
                                if scores_of_battle[i] is not None) / len(scores))

            # For each possible rank of the player, count the number of battles where she had the given rank.
            frequencies = [0] * len(names)
            for scores_of_battle in scores:
                scores_of_battle_no_none = [-x if x is not None else float('inf') for x in scores_of_battle]
                rank = sorted(scores_of_battle_no_none).index(scores_of_battle_no_none[i])
                frequencies[rank] += 1

            # Print the results
            print()
            print('Results for Player', name)
            print('Number of battles', len(scores))
            print('Battles without error:', len(scores) - nb_loss)
            print('Average score:', avg_score)
            print('Ranking:')
            for i, f in enumerate(frequencies):
                print('Rank', i + 1, ':', f)
