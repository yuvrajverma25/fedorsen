
function openPopup() {
    document.getElementById('popup').style.display = 'block';
}

// Function to close the popup
function closePopup() {
    document.getElementById('popup').style.display = 'none';
}


// Attach click event listeners to the buttons
var buttons = document.getElementsByClassName('openPopupButton');
    for (var i = 0; i < buttons.length; i++) {
        buttons[i].addEventListener('click', openPopup);
    }

document.getElementById('closePopupButton').addEventListener('click', closePopup);