function playMusic() {
    let action = document.getElementById('id_play_music').innerHTML;
    console.log(action)
    if (action == 'Pause') {
        document.getElementById('myAudio').pause();
        document.getElementById('id_play_music').innerHTML = 'Play';
    }
    else {
        document.getElementById('myAudio').play();
        document.getElementById('id_play_music').innerHTML = 'Pause';
    }
}