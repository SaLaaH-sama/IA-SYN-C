import gzip
from io import StringIO
from unittest.mock import patch

from src.referee import predefined_msg
from src.gui.shapes import *
from src.referee.logs import *
import json
import html
from src.sync.executor_sync import get_program_execution_iterator, check_program
from src.sync.execution_exceptions import ExecutionError
from src.sync.converter_sync import int_to_bin, float_to_bin, bool_to_bin, char_to_bin, bin_to_string


class Referee(ABC):
    """
     Abstract class representing a game. The players of the game are represented by the class {@link Player} containing
     a SYN-C script. The scripts and the Referee communicate using standard input, output and errors, so that the
     Referee can send information to the players and the player can react by sending commands.

     For each new game, a referee extending this class should be called.
     The classe contains the following public methods :
     - play(), that should be called first to play a new game, it should not be overwritten.
     - get_json() and write_result_to_string to build a JSON object or write it to a file containing all
     the informations of the game (for each turn of the game, standard ouput, errors, information sent to the players
     and the graphics).
     - get_play_by_id(int) to get the player instance knowing its id
     - add_graphic(shape), add_graphics(shapes) to populate the graphical interface of the game with SVG shapes.

     It contains the following protected methods that can be overwritten.
     - add_player(name, script) that takes the name of the player, a script filename as
     input.
     - get_x_min() that returns the minimum x-coordinate of the SVG drawing. The default value is 0.
     - get_x_max() that returns the maximum x-coordinate of the SVG drawing. The default value is 2000.
     - get_y_min() that returns the minimum y-coordinate of the SVG drawing. The default value is 0.
     - get_y_max() that returns the maximum y-coordinate of the SVG drawing. The default value is 1000.
     - get_ms_per_turn() that returns the basic number of millisecond for the animation of a turn. The default value is
     500.

     Finally it contains the following abstract protected methods that must be overwritten:
     - four methods get_x_min(), get_x_max(), get_y_min(), get_y_max() to set the four bounds of the graphics of the
     game.
     - init() to initialize the referee object at the beginning of the game. In order to play multiple games
     with the same Referee object, attributes should be built or reinitialize when the init() function is called.
     - game_turn(int) that executes a turn of the game.
    """

    def __init__(self):
        #  List of players of the current game
        self._players = []

        #  List of graphics of the current game
        self._graphics = []

        #  List containing, for each turn, the map associating, for each player, the standard outputs of the player
        #  at that turn
        self._stdouts = []

        #  List containing, for each turn, the map associating, for each player, the standard errors of the player
        #  at that turn
        self._stderrs = []

        #  List containing, for each turn, the map associating for each player, the list of information sent to
        #  the player by the referee at that turn
        self._game_infos = []

        # Map containing, for each player, the last turn of that player
        self._last_turns = dict()

    def play(self, players_scripts):
        """
        Play a new game with the players represented by the script in the list players_scripts
        :param players_scripts : map associating the name of the player to her script, each script should be a SYN-C
        file
        """
        del self._players[:]
        del self._graphics[:]
        del self._stdouts[:]
        del self._stderrs[:]
        del self._game_infos[:]
        self._last_turns.clear()

        Shape.reset_ids()

        for player_id, (player_name, script) in enumerate(players_scripts.items()):
            player = Player(player_id, player_name, script)
            self._players.append(player)

        for player in self.players:
            if not player.valid_program:
                player.send_game_infos(predefined_msg.INVALID_PROGRAM % str(player.program_error))
                self._last_turns[player] = 1
                player.loose()

        self._init()

        turn = 1

        while True:
            # Play until every player won or loose
            log_general_msg("Start turn " + str(turn))

            # Keep the set of playing players at the beginning of the turn
            not_ended_players = set([player for player in self._players if player.is_playing])

            self._game_turn(turn)

            stdout_of_turn = dict()
            stderr_of_turn = dict()
            game_infos_of_turn = dict()

            for player in self._players:
                # Register the standard output and errors and the information sent by/to the player during this turn

                stdout_of_turn[player] = player.get_stdout_of_last_turn()
                stderr_of_turn[player] = player.get_stderr_of_last_turn()
                game_infos_of_turn[player] = player.get_game_infos_of_last_turn()

                # Check if player ended during this turn
                if player in not_ended_players:
                    if player.is_playing:
                        self._last_turns[player] = turn

            self._stdouts.append(stdout_of_turn)
            self._stderrs.append(stderr_of_turn)
            self._game_infos.append(game_infos_of_turn)

            turn += 1
            if all(not player.is_playing for player in self.players):
                break

        self._end()
        for player in self._players:
            log_results_msg(player, player.score)

    def _get_x_min(self):
        """
        :return: the leftmost abcissa of the graphics of the game. The default value is 0.
        """
        return 0

    def _get_y_min(self):
        """
        :return: the topmost ordinate of the graphics of the game. The default value is 0.
        """
        return 0

    def _get_x_max(self):
        """
        :return: the rightmost abcissa of the graphics of the game. The default value is 2000.
        """
        return 2000

    def _get_y_max(self):
        """
        :return: the bottommost ordinate of the graphics of the game. The default value is 1000.
        """
        return 1000

    def _get_animation_ms_per_turn(self):
        """
        :return: the basic number ms of millisecond of the animation of a turn. The user can change that value
        during the animation  between ms / 5 and ms * 2, with a step of ms / 5. The default value is 500.
        """
        return 500

    def _get_svg(self):
        """
        :return: all the shapes of the game as SVG tags.
        """
        return [shape.to_svg() for shape in self._graphics if not shape.has_parent]

    def _get_animation(self):
        """
        Each animation is encoded using keyframes.

        For each shape and each attribute, a keyframe can be set to fix the attribute at some period of time.
        All those animations are synthesized in a big list organized this way:
        - each item of the list correspond to a turn, it contains all the animations of all the shapes during that turn
        - Such an item is a map, associating to each shape (the key is the name and the id of the shape) the animations
        of the shape during that turn.
        - The value associated with a shape is also a map, associating to moments a keyframe of one or more attributes
        of the shape. The moment m is necessarily a time between 0 and 1. If the animation occurs during turn t, the
        keyframe occurs at time (t + m) (assuming that each turn lasts 1 second).
        - Each keyframe is a map associating to each attribute a value. The animation should be set such that, at the
        moment t + m, the attribute has the corresponding value.

        Remarks :
        - the interpolation between two successive keyframes of a same turn is linear.
        - there is no interpolation between two keyframes occuring in two distinct turns : it is like, in some way, the
        first and the last key frames are duplicated at time t and t + 1 - epsilon.
        Consequently, if a keyframe is set exactly at time t, then the animation joining the last keyframe of turn t - 1
        and that keyframe is instantaneous.

        :return the list of animations
        """
        animations = []
        for shape in self._graphics:
            animations_of_shape = shape.to_animation()

            if animations_of_shape is None:
                continue

            for _ in range(len(animations_of_shape) - len(animations)):
                animations.append(None)

            for i, animation_of_shape in enumerate(animations_of_shape):
                if animation_of_shape is None or len(animation_of_shape) == 0:
                    continue
                animation = animations[i]
                if animation is None:
                    animation = dict()
                    animations[i] = animation
                animation[shape.name + str(shape.id)] = animation_of_shape

        return animations

    @classmethod
    def get_name(cls):
        """
        :return: the name of the game
        """
        klass_name = cls.__name__
        if klass_name.endswith('Referee'):
            klass_name = klass_name[:-7]
        return ''.join(c if c.islower() else (' ' + c) for c in klass_name)

    @classmethod
    def get_filename(cls):
        """
        :return: the filename of the game
        """
        klass_name = cls.__name__
        if klass_name.endswith('Referee'):
            klass_name = klass_name[:-7]
        result = ''.join(c if c.islower() else ('_' + c.lower()) for c in klass_name)
        if klass_name[0].isupper():
            result = result[1:]
        return result

    @staticmethod
    @abstractmethod
    def get_author():
        """
        :return: the name of the author
        """
        pass

    @staticmethod
    @abstractmethod
    def get_description():
        """
        :return: a short description of the game.
        """
        pass

    @staticmethod
    @abstractmethod
    def allowed_number_of_players():
        """
        :return: a list of the allowed number of players of a game played by this referee. For instance, returning
        [2, 4] means that the game can be played by 2 or 4 players, but not 3.
        """
        pass

    def get_json(self):
        """
        :return: a JSON object containing all the informations of the game (for each turn of the game, standard ouput,
        errors, information sent to the players and the graphics).
        """
        json_object = dict()

        json_infos = dict()
        json_object['infos'] = json_infos
        json_infos['nbPlayers'] = len(self._players)
        json_infos['playersNames'] = [player.name for player in self._players]
        json_infos["playersLastTurns"] = [self._last_turns.get(player, -1) for player in self._players]
        json_infos["name"] = self.get_name()
        json_infos["msPerTurn"] = self._get_animation_ms_per_turn()

        json_object['scores'] = [player.score for player in self._players]

        json_svg_infos = dict()
        json_object["svgInfos"] = json_svg_infos
        json_svg_infos["xMin"] = self._get_x_min()
        json_svg_infos["xMax"] = self._get_x_max()
        json_svg_infos["yMin"] = self._get_y_min()
        json_svg_infos["yMax"] = self._get_y_max()

        json_object["stdout"] = [[stdout_of_turn[player] for player in self._players]
                                 for stdout_of_turn in self._stdouts]
        json_object["stderr"] = [[stderr_of_turn[player] for player in self._players]
                                 for stderr_of_turn in self._stderrs]
        json_object["gameInfos"] = [[game_infos_of_turn[player] for player in self._players]
                                    for game_infos_of_turn in self._game_infos]
        # Repeat last gameInfos message until the last turn
        jogi = json_object["gameInfos"]
        for i, player in enumerate(self.players):
            for j, game_infos_of_turn in enumerate(reversed(jogi)):
                last_msg = game_infos_of_turn[i]
                if last_msg.strip() != '':
                    break
            else:
                continue
            for game_infos_of_turn in jogi[len(jogi) - j:]:
                game_infos_of_turn[i] = last_msg

        json_object["svg"] = ''.join(self._get_svg())
        json_object["animations"] = self._get_animation()

        return json.dumps(json_object)

    def write_results_to(self, filename):
        """
        Write the JSON file returned by get_json to the given file
        :param filename: path to the file where to write the JSON file
        """
        with open(filename, 'w') as f:
            f.write(self.get_json())

    def compress_results_to(self, filename):
        """
        Write a GZIP compressed version of the JSON file returned by get_json to the given file
        :param filename: path to the file where to write the compressed JSON file
        """
        with gzip.open(filename, 'wt') as f:
            f.write(self.get_json())

    @property
    def players(self):
        return self._players

    @abstractmethod
    def _init(self):
        """
        Actions that should be done at the beginning of the game to initialize some parameters or fields
        """
        pass

    @abstractmethod
    def _end(self):
        """
        Actions that should be done at the end of the game to close some parameters or fields
        """
        pass

    @abstractmethod
    def _game_turn(self, turn):
        pass

    def get_player_by_id(self, player_id):
        """
        :param player_id: id of a player
        :return: the player for which the id is the given id
        """
        return self._players[player_id]

    def get_player_by_name(self, player_name):
        """
        :param player_name: name of a player
        :return: the player for which the name is the given name
        """
        for player in self._players:
            if player.name == player_name:
                return player
        return None

    def add_graphic(self, shape):
        """
        Add the given shape to the graphical shapes of the referee, that should be displayed in the game viewer.
        If a shape is a group (from the class Group), every descendant of the group is added.
        Thus, this function should not be called to add the descendants of the group to the view.

        :param shape: a SVG shape
        """
        # A list is used to keep the ordering
        if shape in self._graphics:
            return
        self._graphics.append(shape)
        if type(shape) is not Group:
            return

        for child in shape.children:
            self.add_graphic(child)

    def add_graphics(self, shapes):
        """
        Add the given shapes to the graphical shapes of the referee, that should be displayed in the game viewer.
        If a shape is a group (from the class {@link Group}), every descendant of the group is added.
        Thus, this function should not be called to add the descendants of the group to the view.
        :param shapes: a collection of SVG shapes
        """
        for shape in shapes:
            self.add_graphic(shape)


class Player:
    """
    Class representing a player of a game.
    The player class is the interface between the abstract Referee class and the scripts written by the (real)
    players.

    It contains the following public getter methods:
    - id (getter through @property) returns the id of the player
    - name (getter through @property) returns the player

    It contains the following methods to communicate with the script:
    - get_output_line() execute the script until one line from the standard output of the script is sent
    An exception is sent if the script uses too many elementary operations to print the result
    - set_input_line_nl(params) and the static set_input_line_nl_to_all_players(players, params) to send
    one line to the standard input of the script or all the scripts

    It contains the following methods about the ending of the game of a player:
    - win(score) to make a player winning the game. In that case a score is set. The highest score is a winning
    score.
    - loose() to make the player loosing the game
    - is_playing (as a property) to known if a player continues to play
    - hast_lost to known if a player has lost the game

    It contains the other following useful methods:
    - send_game_infos(msg) to register an information about the player (usually an error due to a prohibited
    command of the player, or a message to explain why a player won/loose).
 """

    # Maximum number of elementary operations that can be used before the first output
    FIRST_MAX_ELEMENTARY_OPERATIONS_TIMEOUT = 500000

    # Maximum number of elementary operations that can be used between two outputs
    MAX_ELEMENTARY_OPERATIONS_TIMEOUT = 30000

    # Limit for the player DEBUG messages each turn
    DEBUG_LIMIT = 600

    _nb_players = 0

    def __init__(self, player_id, player_name, player_script_filename):
        """
        :param player_id: Id of the player
        :param player_name: Name of the player
        :param player_script_filename: Script filename of the player. The script should be a SYN-C script.
        It is assumed that the script does not contain any non-execution error. It is well formed, contains a main
        function, ...
        """
        # Id of the player
        self._id = player_id

        # Name of the player
        self._name = player_name

        self._script_filename = player_script_filename

        try:
            check_program(program_filename=player_script_filename)
            self.program = get_program_execution_iterator(program_filename=player_script_filename)
            self._program_error = None
        except Exception as e:
            self.program = None
            self._program_error = str(e)

        # The list of bits that will be sent to the player if he uses the READ() command
        # Each string of this list contain exactly 32 bits and no other character.
        self._stdin_of_this_turn = []

        # The list of strings printed by the PRINT command of the player
        self._stdout_of_this_turn = []

        # The list of strings printed by the PRINTERR command of the player
        self._stderr_of_this_turn = []

        # The information concerning the game and the player during the current turn of the game
        self._game_infos_of_this_turn = []

        # Flag, true if the player won or loosed
        self._ended = False

        # Flag, true if the player loosed
        self._loose = False

        # Score of the player
        self._score = 0

        # Flag, true if the first output of the player was not already read.
        self.first_time_out = True

        Player._nb_players += 1

    @property
    def id(self):
        return self._id

    @property
    def name(self):
        return self._name

    @property
    def valid_program(self):
        return self._program_error is None

    @property
    def program_error(self):
        return self._program_error

    def get_output_line(self):
        """
        Execute the script of the player until one line from the standard output of the given player is sent.

        If the player does not return any line during some number of elementary operations, or if an error occured
        during the execution, None is returned instead ; in addition, the player is ended (with a 'loose' status).
        The timeout is FIRST_MAX_ELEMENTARY_OPERATIONS_TIMEOUT if this is the first time the function is
        called, and MAX_ELEMENTARY_OPERATIONS_TIMEOUT otherwise.

        :return the line outputted by the player
        """

        timeout = self._timeout
        self.update_timeout()

        def get_next_input():
            return self._stdin_of_this_turn.pop(0)

        no_input_msg = False
        execution_error = None
        end_of_program = False

        with patch('sys.stdout', new=StringIO()) as result_out:
            with patch('sys.stderr', new=StringIO()) as result_err:
                with patch('builtins.input', get_next_input):
                    iteration = 0
                    node_line = -1
                    node_char = -1

                    while len(result_out.getvalue()) == 0 and iteration < timeout:
                        try:
                            node_line, node_char = next(self.program)
                            iteration += 1
                        except IndexError:
                            # If the player asked for input() but no such input exist
                            no_input_msg = True
                            break
                        except ExecutionError as e:
                            # If the script of the player sent an error
                            execution_error = e
                            break
                        except StopIteration:
                            # If the script of the player ended
                            end_of_program = True
                            break

        # We get the output and remove the trailing newline
        output = result_out.getvalue().strip()
        self._stdout_of_this_turn.append(output)
        log_output_msg(self, output)

        # We get the standard error and remove the trailing newline
        # Also a limit on the number of characters is given
        for err_msg in result_err.getvalue().strip()[:Player.DEBUG_LIMIT].split('\n'):
            self._stderr_of_this_turn.append(err_msg)
            log_debug_msg(self, err_msg)

        if no_input_msg:
            self.loose()
            self.send_game_infos(predefined_msg.NO_INPUT_MSG_ERROR)
            self.send_game_infos("Last Line : %s ; Last char in line : %s " % (node_line, node_char))
            return None
        elif execution_error is not None:
            self.loose()
            self.send_game_infos(str(execution_error))
            return None
        elif end_of_program:
            iteration = timeout
            node_line = 'End of the program'
            node_char = 'N/A'

        if iteration >= timeout:
            self.loose()
            self.send_game_infos(predefined_msg.TIMEOUT_MSG_ERROR)
            self.send_game_infos("Last Line : %s ; Last char in line : %s " % (node_line, node_char))
            return None

        # Return the output
        return output

    @staticmethod
    def get_output_line_from_all_players(players):
        """
        Execute the script of each player of players until one line from the standard output of the given player is
        sent.

        If the player does not return any line during some number of elementary operations, or if an error occured
        during the execution, None is get instead.
        The timeout is FIRST_MAX_ELEMENTARY_OPERATIONS_TIMEOUT if this is the first time the function is
        called, and MAX_ELEMENTARY_OPERATIONS_TIMEOUT otherwise.

        :return a map associating each player to the returned output
        """
        return {player: player.get_output_line() for player in players}

    @property
    def _timeout(self):
        """
        :return: the elementary operations timeout depending if this is the first turn of the player or not.
        """
        if self.first_time_out:
            return Player.FIRST_MAX_ELEMENTARY_OPERATIONS_TIMEOUT
        else:
            return Player.MAX_ELEMENTARY_OPERATIONS_TIMEOUT

    def update_timeout(self):
        """
        Update the player so that the elementary operations timeout becomes MAX_ELEMENTARY_OPERATIONS_TIMEOUT.
        """
        self.first_time_out = False

    def send_game_infos(self, game_infos):
        """
        Register an information about the game and the player arising during the current turn of the game.
        :param game_infos: the information to be sent to the user.
        :return:
        """
        self._game_infos_of_this_turn.append(game_infos)

    def send_input_line_nl(self, input_msg):
        """
        Send all the given inputs to the standard input of the player. Each input must be a 32 bits binary string.
        :param input_msg: the input to be sent the player or a list of inputs.
        In that last case, the game send each input in the list to the player.
        """
        if type(input_msg) not in (list, tuple):
            input_msg = [input_msg]
        self._send_input_line_nl_with_log(True, input_msg)

    @staticmethod
    def send_input_line_nl_to_all_players(players, input_msg, all_players=True):
        """
        Send all the given inputs to the standard input of the given players.
        Each input must be a 32 bits binary string.

        :param players: list of players to which the message is send
        :param input_msg: the input to be sent the players, or a list of inputs.
        In that last case, the game send each input in the list to the players.
        :param all_players: true if all the players are in the players list. If players may not contain all the players,
         set to false.
        """
        if type(input_msg) not in (list, tuple):
            input_msg = [input_msg]

        if all_players:
            log_input_msg(None, ' '.join([str(x) for x in input_msg]))

        for player in players:
            player._send_input_line_nl_with_log(not all_players, input_msg)

    def _send_input_line_nl_with_log(self, log, input_msg):
        if log:
            log_input_msg(self, ' '.join([str(x) for x in input_msg]))

        bin_msg = 0
        for input_value in input_msg:
            t = type(input_value)
            if t is int:
                bin_msg = int_to_bin(input_value)
            elif t is float:
                bin_msg = float_to_bin(input_value)
            elif t is bool:
                bin_msg = bool_to_bin(input_value)
            elif t is str:
                if len(input_value) == 0:
                    input_value = '\0'
                bin_msg = char_to_bin(input_value[0])

            self._stdin_of_this_turn.append(bin_to_string(bin_msg))

    def win(self, score):
        """
        End the game of the player, set the player as a winner and set his score.
        :param score: the score of the winning player
        """
        self._end(score, False)

    def loose(self):
        """
        End the game of the player, set the player as a looser. Such a player has no score.
        """
        self._end(-1, True)

    def _end(self, score, loose):
        """
        End the game of the player, set the player as a looser iff the player loosed the game, and set the score of the
        player
        """
        self._ended = True
        self._score = score
        self._loose = loose

    @property
    def is_playing(self):
        """
        :return: true if and only the player has not loosed or won the game, meaning that the player continues to play
       (and that the functions win and loose were not called.
        """
        return not self._ended

    @property
    def has_lost(self):
        """
        :return: true if and only the player has loosed the game.
        """
        return self._loose

    @property
    def score(self):
        """
        :return: the score of the player. The highest score is a winning score. 
        """
        return self._score

    def get_stdout_of_last_turn(self):
        """
        :return: All the strings sent to the standard output during this turn by the player
        """
        stdout = '<br/>'.join((html.escape(s) for s in self._stdout_of_this_turn))
        del self._stdout_of_this_turn[:]
        return stdout

    def get_stderr_of_last_turn(self):
        """
        :return: All the strings sent to the standard error during this turn by the player (up to the limit of DEBUG
        LIMIT)
        """
        stderr = '<br/>'.join((html.escape(s) for s in self._stderr_of_this_turn))
        del self._stderr_of_this_turn[:]
        return stderr

    def get_game_infos_of_last_turn(self):
        """
        :return: All the strings sent to the player by the game during this turn
        """
        game_infos = '<br/>'.join(self._game_infos_of_this_turn)
        log_game_msg(self, game_infos)
        del self._game_infos_of_this_turn[:]
        return game_infos

    def __str__(self):
        return self._script_filename

    def __repr__(self):
        return self._script_filename
