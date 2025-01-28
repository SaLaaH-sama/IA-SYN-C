<!DOCTYPE html>

<?php

    // Load the JSON file containing the description of the animation of the game
    $json_file = file_get_contents("./results.json");
    $json = json_decode($json_file);
?>

<html>
<head>

    <title><?php echo $json->infos->name; ?></title>
    <meta name="description" content="Jeu de combat de bots à coder.">
    <meta name="author" content="Dimitri Watel">

    <link rel="stylesheet" href="style.css">

    <!-- Load the necessary libraries to animate the game -->
    <script src="https://code.jquery.com/jquery-3.4.1.min.js"
      integrity="sha256-CSXorXvZcTkaix6Yvo6HppcZGetbYMGWSFlBw8HfCJo="
      crossorigin="anonymous"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/velocity/1.5.2/velocity.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/velocity/1.5.2/velocity.ui.min.js"></script>
</head>
<body>
    <div class="battle">
        <div id="display"> <!-- Display of the title of the game, the animated graphics of the game and the player -->
            <div class="gameTitle"><span><?php echo $json->infos->name; ?></span></div> <!-- Title of the game -->
            <div class="animation"> <!-- Graphics of the game -->
                <svg id="gameImage" version="1.1" viewBox="<?php echo $json->svgInfos->xMin;
                ?> <?php echo $json->svgInfos->yMin;?> <?php echo $json->svgInfos->xMax;
                ?> <?php echo $json->svgInfos->yMax;?>">
                    <?php
                        // We remove from the svg every tag not corresponding to a SVG shape or text
                        // Particularly, the script tag is removed.
                        // We avoid any malicious injection from the JSON. 
                        // TODO : remove inline javascript attributes
                        echo strip_tags($json->svg, "<path><line><rect><ellipse><polygon><polyline><text><g>");
                    ?>
                </svg>
            </div>
            <div class="player"> <!-- Player on the bottom left part, allow to play, pause, fullscreen ... the animated graphics of the game -->
                <svg id="playerImage" version="1.1" width="750" height="70">
                    <circle id="playerLeft" cx="30" cy="30" r="20" fill="white" stroke="black" stroke-width="3" onclick="previous()"/>
                    <circle id="playerPause" cx="80" cy="30" r="20" fill="white" stroke="gray" stroke-width="3" onclick="pause()"/>
                    <circle id="playerPlay" cx="130" cy="30" r="20" fill="white" stroke="black" stroke-width="3" onclick="play()"/>
                    <circle id="playerRight" cx="180" cy="30" r="20" fill="white" stroke="black" stroke-width="3" onclick="next()"/>

                    <polyline id="playerLeftIcon" points="38 15, 15 30, 38 45" fill="none" stroke="black" stroke-width="3" onclick="previous()"/>
                    <g id="playerPauseIcon" fill="gray" onclick="pause()">
                        <rect x="73" y="18" width="5" height="24"/>
                        <rect x="82" y="18" width="5" height="24"/>
                    </g>
                    <polygon id="playerPlayIcon" points="120 15, 145 30, 120 45" opacity="1" fill="black" onclick="play()"/>
                    <polyline id="playerRightIcon" points="172 15, 195 30, 172 45" fill="none" stroke="black" stroke-width="3" onclick="next()"/>

                    <rect id="playerBar" x="230" y="25" width="300" height="10" fill="white" stroke="black"
                    stroke-width="3" onclick="clickOnProgressBar(event)" />
                    <rect id="playerProgress" x="230" y="25" width="0" height="10" fill="black"
                    onclick="clickOnProgressBar(event)" />
                    <polygon id="playerProgressPointer" points="230 37, 240 47, 220 47" fill="black"/>
                    <text id="playerProgressText" x="230" y="60" text-anchor="middle" dominant-baseline="middle">1</text>

                    <circle id="playerSlow" cx="580" cy="30" r="20" fill="white" stroke="black" stroke-width="3" onclick="slower()"/>
                    <circle id="playerFast" cx="630" cy="30" r="20" fill="white" stroke="black" stroke-width="3" onclick="faster()"/>
                    <polygon id="playerSlowIcon" points="577 17, 565 30, 577 45, 577 30, 589 43, 589 17, 577 30" fill="none" stroke="black" stroke-width="3" onclick="slower()"/>
                    <polygon id="playerFastIcon" points="633 17, 645 30, 633 45, 633 30, 621 43, 621 17, 633 30" fill="none" stroke="black" stroke-width="3" onclick="faster()"/>

                    <rect id="playerFullScreen" x="700" y="15" width="40" height="30" fill="white" stroke="black" stroke-width="3" onclick="toggleFullScreen()"/>
                    <polyline points="695 20, 695 10, 705 10" fill="none" stroke="black"/>
                    <polyline points="745 40, 745 50, 735 50" fill="none" stroke="black"/>
                </svg>
            </div>
        </div>
        <div class="informations"> <!-- Right side of the game, display the stdout, stderr, and information of the game sent to or by the players -->
            <div class="names"><!-- Names of the players --><?php
                    for($i = 0 ; $i < $json->infos->nbPlayers; $i++){
                ?><div class="name">
                <span><strong>J<?php echo $i; ?> <?php echo $json->infos->playersNames[$i]; ?></strong></span>
                </div><?php
                    }
                ?></div>
            <div class="stdouts"><!-- Standard outputs of the players -->
                <span><strong>Sortie standard</strong></span><br/><?php
                    for($i = 0 ; $i < $json->infos->nbPlayers; $i++){
                ?><div class="stdout">
                    <span class="stdoutText" id="stdout<?php echo $i;?>"></span>
                </div><?php
                    }
                ?></div>
            <div class="stderrs"> <!-- Standard errors of the players -->
                <span><strong>Debug</strong></span><br/><?php
                    for($i = 0 ; $i < $json->infos->nbPlayers; $i++){
                ?><div class="stderr">
                    <span class="stderrText" id="stderr<?php echo $i;?>"></span>
                </div><?php
                    }
                ?></div>
            <div class="gameInformations"> <!-- Information sent by the game to the players (particularly the errors) -->
                <span><strong>Informations du jeu</strong></span><br/><?php
                    for($i = 0 ; $i < $json->infos->nbPlayers; $i++){
                ?><div class="gameInformation">
                    <span class="gameInformationText" id="gameInformation<?php echo $i;?>"></span>
                </div><?php
                    }
                ?></div>
        </div>
    </div>
<script>

        // Global variables
        
        // Durations of the turns of the animation (in milliseconds). The duration can be changed by clicking on the "fast/slow" icons on the player. It
        // cannot be below $minMsPerTurn and above $maxMsPerTurn. When clicking, the duration changes by deltaMsPerTurn. 
        // $msPerTurn is the current value of the duration
        // $expectedMsPerTurn is the next value of the duration. When a button is clicked, the duration is not changed immediately to avoid some animation shifting
        // of gaps problems. It waits for the end of the turn and then change the value of the duration according to the value of $expectedMsPerTurn.
        $msPerTurn = <?php echo $json->infos->msPerTurn; ?>;
        $minMsPerTurn = $msPerTurn / 5;
        $maxMsPerTurn = $msPerTurn * 2;
        $deltaMsPerTurn = $msPerTurn / 5;
        $expectedMsPerTurn = $msPerTurn;

        // A timer repeateadly calls the #animate function. Each call animate one turn of the game during $msPerTurn ms. 
        // The duration between two calls is $turnIntervalRatio * $msPerTurn
        $turnIntervalRatio = 1.05;

        // A flag, true iff the animation is playing.
        $playing = false;

        // JSON containing all the information of the game
        $json = null;

        // Number of players of the game
        $nbPlayers = null;

        // Order strings so that "translateX" and "translateY" are placed first
        function orderKeys(key1, key2) {
            if(key1 === "translateX")
                return -1;
            else if (key2 === "translateX")
                return 1;
            else if(key1 === "translateY")
                return -1;
            else if (key2 === "translateY")
                return 1;
            else if (key1 < key2) return -1;
            else if (key1 > key2) return +1;
            else return 0;
        }

        // Load the JSON
        $.getJSON("./results.json", function(json) {

            $json = json
            $nbPlayers = json.infos.nbPlayers;
            $turn = -1;

            // Display the initial state of the game.
            setTurn(0);
        });


        /** Animate one turn of the game */
        function animate(){
            console.log("Animate", $turn);


            // Update the stdout, debug and info parts of the game
            setInfos();
            

            // If the end of the game is reached
            if($turn >= $json.animations.length){
                pause();
                // Check if the user clicked on the player to accelerate or slow down the animation. 
                checkMsPerTurn();
                return;
            }

            // Get all the information of the animation of this turn
            var animationsOfTurn = $json.animations[$turn];


            // null if nothing should be animated this turn
            if(animationsOfTurn == null){
                // Check if the user clicked on the player to accelerate or slow down the animation. 
                checkMsPerTurn();
                return;
            }

            // For each element that should be animated
            for(var id in animationsOfTurn){
                let element = $("#" + id);

                // The animation of the element is stored as a succession of pair time/[list of pairs attribute/value], saying that "at that time, 
                // each attribute of the list should be with the associated value". The interpolation between two succesive times t1 and t2 is linear. 
                // If an attribute is not in the list, it should remain unchanged between t1 and t2.
                // Sometimes, the list is empty. In that case, nothing should be change during t2 - t1. 
                // Instead of running an animation doing nothing during t2 - t1, we increase the delay by t2 - t1 and the next animation doing something 
                // will wait t2 - t1 before starting. 
                let delay = 0; 

                // Every attribute that should be animated. 
                let animationsOfElement = animationsOfTurn[id];

                // Previous time
                let previousSubTurn = 0;

                // Sort the times of each pair of the list. 
                Object.keys(animationsOfElement).sort().forEach(function(subturn) {
                    let animationOfElement = animationsOfElement[subturn];

                    // Duration of the current animation
                    let delta = subturn - previousSubTurn;
                    previousSubTurn = subturn;

                    // If nothing should be animated we increase the delta
                    if(Object.keys(animationOfElement).length === 0){
                        delay += delta;
                        return;
                    }


                    // A copy is made to leave the json unchanged
                    // The key are sorted so that the "translateX" and "translateY" keys are placed first
                    var key = Object.keys(animationOfElement)
                    .sort(orderKeys);

                    let animationOfElementCopy = {};
                    for (var i = 0; i < key.length; i++)
                        animationOfElementCopy[key[i]] = animationOfElement[key[i]];


                    // The text cannot be animated.
                    // If it should be animated, we use the #complete callback to change the value at the end of the animation
                    if("text" in animationOfElement){
                        // We remove the "text" attribute from the animation
                        let textValue = animationOfElementCopy["text"];
                        delete animationOfElementCopy["text"];

                        // A dummy change is added, velocity does not accept the empty list as input 
                        if(Object.keys(animationOfElementCopy).length === 0)
                            animationOfElementCopy["opacity"] = "+=0";


                        element.velocity(animationOfElementCopy,
                        {
                            delay: delay * $msPerTurn,
                            duration:delta * $msPerTurn,
                            ease:"linear",
                            complete: function(e){
                                $("#" + e[0].id).text(textValue);
                            }
                        });
                    }
                    else{


                        element.velocity(animationOfElementCopy,
                        {
                            delay: delay * $msPerTurn,
                            duration: delta * $msPerTurn,
                            ease: "linear"
                        });
                    }

                    delay = 0;
                });

            }
            
            $turn += 1;
            // Update the progress bar of the player
            setProgressBar();


            // Check if the user clicked on the player to accelerate or slow down the animation. 
            checkMsPerTurn();
        }

        /** Update the stdout, debug and info parts of the game according to the values of the current turn */
        function setInfos(){
            for(var i = 0; i < $nbPlayers; i++){
                var stdout = $("#stdout" + i);
                var stderr = $("#stderr" + i);
                var gameInfos = $("#gameInformation" + i);

                if($turn < $json.stdout.length)
                    stdout.html($json.stdout[$turn][i]);

                if($turn < $json.stderr.length)
                    stderr.html($json.stderr[$turn][i]);

                if($turn < $json.gameInfos.length)
                    gameInfos.html($json.gameInfos[$turn][i]);
            }
        }

        /** Update the progress bar of the player according to the current value of the turn */
        function setProgressBar(){
            var w = Number($("#playerBar").attr("width"));
            var dx = w / ($json.animations.length);
            var progress = $("#playerProgress");

            var pw = Number(progress.attr("width"));
            var x = Number(progress.attr("x"));
            var nw = dx * $turn;
            progress.attr("width", nw);

            var nx = x + nw;
            var pointer = $("#playerProgressPointer");
            pointer.attr("points", nx + " 37, " + (nx + 10) + " 47, " + (nx - 10) + " 47");

            var text = $("#playerProgressText");
            text.attr("x", nx);
            text.text($turn + 1);
        }

        /** Check if the user asked to accelerate or decelerate the duration of the turn.*/
        function checkMsPerTurn(){
            if($msPerTurn == $expectedMsPerTurn)
                return;
            clearInterval($timerInterval);
            $msPerTurn = $expectedMsPerTurn;
            $timerInterval = setInterval(animate, $msPerTurn * $turnIntervalRatio);
        }

        /** Change the display of the game as if it was animated from the beggining during the given number of turns instantaneously. 
          * used when the user click on "next frame, previous frame" or on the progress bar. 
          * */
        function setTurn(turn){
            if($playing)
                return;

            $turn = turn;

            // Update the stdout, debug and info parts of the game
            setInfos();
            // Update the progress bar of the player
            setProgressBar();

            // For each element, compute the value of the attributes of that element at the given turn
            var animationSynthesis = {};
            turn = 0;
            while(true){
                let animationsOfTurn = $json.animations[turn];

                for(let id in animationsOfTurn){
                    let element = $("#" + id);

                    if(animationsOfTurn == null)
                        continue;

                    if(!(id in animationSynthesis))
                        animationSynthesis[id] = {};

                    if($turn == 0){
                        let animationsOfElement = animationsOfTurn[id];
                        let animationOfElement = animationsOfElement["0.0"];
                        Object.keys(animationOfElement).forEach(function(attribute){
                            animationSynthesis[id][attribute] = animationOfElement[attribute];
                        });
                    }
                    else{
                        let animationsOfElement = animationsOfTurn[id];
                        Object.keys(animationsOfElement).sort().forEach(function(subturn) {
                            let animationOfElement = animationsOfElement[subturn];
                            Object.keys(animationOfElement).forEach(function(attribute){
                                animationSynthesis[id][attribute] = animationOfElement[attribute];
                            });
                        });
                    }
                }

                turn++;
                if($turn - 1 < turn)
                    break;

            }

            // For each element play the animation instantaneously.
            // Velocity is used instead of the "attr" jQuery function because some attributes (translate, rotate, scale, fontsize, ...) 
            // are not changed the same way with the two functions.
            for(let id in animationSynthesis){

                let element = $("#" + id);
                let animationOfElement = animationSynthesis[id];


                // The key are sorted so that the "translateX" and "translateY" keys are placed first
                var key = Object.keys(animationOfElement).sort(orderKeys);

                let animationOfElementCopy = {};
                for (var i = 0; i < key.length; i++)
                    animationOfElementCopy[key[i]] = animationOfElement[key[i]];

                if("text" in animationOfElementCopy){
                    // animationOfElement is already a copy of what is written in the json and can be safely modified.
                    let textValue = animationOfElementCopy["text"];
                    delete animationOfElementCopy["text"];
                    element.text(textValue);
                    if(animationOfElementCopy.length !== 0){
                        element.velocity(animationOfElementCopy,
                        {
                            duration:0,
                            ease:"linear"
                        });
                    }
                }
                else{
                    element.velocity(animationOfElementCopy,
                    {
                        duration: 0,
                        ease: "linear"
                    });
                }
            }
        }

        /** Play the animation, used when the user clicked on play. */
        function play(){
            if($playing)
                return;
            $playing = true;
            $("#playerPlay").attr("stroke", "gray");
            $("#playerPause").attr("stroke", "black");
            $("#playerLeft").attr("stroke", "gray");
            $("#playerRight").attr("stroke", "gray");
            $("#playerPlayIcon").attr("fill", "gray");
            $("#playerPauseIcon").attr("fill", "black");
            $("#playerLeftIcon").attr("stroke", "gray");
            $("#playerRightIcon").attr("stroke", "gray");

            $timerInterval = setInterval(animate, $msPerTurn * $turnIntervalRatio);
        }

        /** Pause the animation, used when the user clicked on pause. */
        function pause(){
            if(!$playing)
                return;
            $playing = false;
            $("#playerPlay").attr("stroke", "black");
            $("#playerPause").attr("stroke", "gray");
            $("#playerLeft").attr("stroke", "black");
            $("#playerRight").attr("stroke", "black");
            $("#playerPlayIcon").attr("fill", "black");
            $("#playerPauseIcon").attr("fill", "gray");
            $("#playerLeftIcon").attr("stroke", "black");
            $("#playerRightIcon").attr("stroke", "black");
            clearInterval($timerInterval);
        }

        /** Display the previous frame of the animation, used when the user clicked on previous. */
        function previous(){
            if($playing)
                return;
            if($turn == 0)
                return;
            if($turn > $json.animations.length)
                $turn = $json.animations.length;
            setTurn($turn - 1);
        }

        /** Display the next frame of the animation, used when the user clicked on next. */
        function next(){
            if($playing)
                return;
            if($turn >= $json.animations.length)
                return;
            setTurn($turn + 1);
        }

        /** Display the turn corresponding to where the user clicked on the progress bar. */
        function clickOnProgressBar(evt){
            if($playing)
                return;

            var e = evt.target;
            var dim = e.getBoundingClientRect();
            var x = evt.clientX - dim.left;

            var w = Number($("#playerBar").attr("width"));
            var dx = w / $json.animations.length;
            var turn = Math.round(x / dx);

            if(turn < 0)
                turn = 0;
            if(turn >= $json.animations.length)
               turn = $json.animations.length;

            setTurn(turn);
        }

        /**
          * Decellerate the animation, used when the user clicked on the slow down button.
         */ 
        function slower(){
            if($expectedMsPerTurn == $maxMsPerTurn)
                return;

            $expectedMsPerTurn += $deltaMsPerTurn;

            $("#playerFast").attr("stroke", "black");
            $("#playerFastIcon").attr("stroke", "black");

            if($expectedMsPerTurn >= $maxMsPerTurn){
                $expectedMsPerTurn = $maxMsPerTurn;
                $("#playerSlow").attr("stroke", "gray");
                $("#playerSlowIcon").attr("stroke", "gray");
            }
        }

        /**
          * Accellerate the animation, used when the user clicked on the faster button.
         */ 
        function faster(){
            if($expectedMsPerTurn == $minMsPerTurn)
                return;

            $expectedMsPerTurn -= $deltaMsPerTurn;

            $("#playerSlow").attr("stroke", "black");
            $("#playerSlowIcon").attr("stroke", "black");

            if($expectedMsPerTurn <= $minMsPerTurn){
                $expectedMsPerTurn = $minMsPerTurn;
                $("#playerFast").attr("stroke", "gray");
                $("#playerFastIcon").attr("stroke", "gray");
            }
        }

        // Toggle the full screen for the animation. 
        function toggleFullScreen() {
            var element = document.getElementById("display");
            console.log(element);
            if (
            !document.fullScreen
            && !document.mozFullScreen
            && !document.webkitIsFullScreen
            && !document.oFullScreen
            && !document.msFullScreen) {
                if (element.requestFullscreen) {
                    element.requestFullscreen();
                } else if (element.mozRequestFullScreen) {
                    element.mozRequestFullScreen();
                } else if (element.webkitRequestFullScreen) {
                    element.webkitRequestFullScreen(Element.ALLOW_KEYBOARD_INPUT);
                } else if (element.msRequestFullscreen) {
                    element.msRequestFullscreen();
                } else if (element.oRequestFullscreen) {
                    element.oRequestFullscreen();
                }
            } else {
                if (document.cancelFullScreen) {
                    document.cancelFullScreen();
                } else if(document.mozCancelFullScreen){
                    document.mozCancelFullScreen();
                } else if(document.webkitCancelFullScreen){
                    document.webkitCancelFullScreen();
                } else if(document.msCancelFullScreen){
                    document.msCancelFullScreen();
                } else if(document.oCancelFullScreen){
                    document.oCancelFullScreen();
                }
            }
        }
    </script>
</body>
</html>
