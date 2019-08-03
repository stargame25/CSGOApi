function displayGame(e) {
    let target = e.path[5].getElementsByClassName("details")[0];
    let animTarget = e.path[5].getElementsByClassName("gameDetails")[0];
    let arrow = e.path[1];
    let icon = e.target;
    e.target.setAttribute("onclick", "");
    if (target.style.display === "flex") {
        arrow.className = "flipAnimBack";
        animTarget.className = "gameDetails animated fadeInDownSlideBack";
        unloadProfileImages(target);
        setTimeout(() => {target.style.display = 'none'}, 1100);
    }
    else {
        arrow.className = "flipAnim";
        animTarget.className = "gameDetails animated fadeInDownSlide";
        target.style.display = 'flex';
        loadProfileImages(target);
    }
    setTimeout(() => {icon.setAttribute("onclick", "displayGame(event)")}, 1100);
}

function playerShowBan(e) {
    let bar = document.getElementById("tooltip");
    let banData = jsonify(e.target.getAttribute("ban"));
    if (banData.length > 0) {
        banData = JSON.parse(banData)[0]
    } else {
        banData = undefined
    }
    if (banData) {
        bar.style.display = 'block';
        bar.innerText = "";
        bar.innerText = bar.innerText + "VAC Ban: " + banData.VAC + "\n";
        bar.innerText = bar.innerText + "Overwatch: " + banData.overwatch + '\n';
        bar.innerText = bar.innerText + "Ban days: " + banData.DaysSinceLastBan + '\n';
        bar.style.top = e.clientY + window.scrollY + 20 + "px";
        bar.style.left = e.clientX + 20 + "px";
    }

}

function tooltipHide(e) {
    let bar = document.getElementById("tooltip");
    bar.style.display = 'none'
}

function loadProfileImages(e) {
    if (e.getElementsByTagName("img").length > 0) {
        target = e.getElementsByTagName("img");
        for (let i = 0; i < target.length; i++) {
            target[i].src = target[i].getAttribute("temp")
        }
    }

}

function unloadProfileImages(e) {
    if (e.getElementsByTagName("img").length > 0) {
        target = e.getElementsByTagName("img");
        for (let i = 0; i < target.length; i++) {
            target[i].src = ""
        }
    }
}

(function listAnimation(){
    list = [...document.getElementsByClassName("game")];
    list.forEach((item, index) => {
        item.style.opacity = 0;
        if(list.length > 50){
            setTimeout(() => {item.className = item.className + " animated fadeIn"}, (5000/list.length * index));
        } else {
            setTimeout(() => {item.className = item.className + " animated fadeIn"}, (index * 100));
        }
    })
})();