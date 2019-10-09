function displayGame(e) {
    let target = e.path[5].getElementsByClassName("details")[0];
    let animTarget = e.path[5].getElementsByClassName("game-details")[0];
    let arrow = e.path[1];
    let icon = e.target;
    e.target.setAttribute("onclick", "");
    if (target.style.display === "flex") {
        arrow.className = "flip-anim-back";
        animTarget.className = "game-details animated fade-in-down-slide-back";
        unloadProfileImages(target);
        setTimeout(() => {target.style.display = 'none'}, 1100);
    }
    else {
        arrow.className = "flip-anim";
        animTarget.className = "game-details animated fade-in-down-slide";
        target.style.display = 'flex';
        loadProfileImages(target);
    }
    setTimeout(() => {icon.setAttribute("onclick", "displayGame(event)")}, 1100);
}

function playerShowBan(e) {
    let bar = document.getElementById("tooltip");
    let banData = JSON.parse(e.target.getAttribute("ban"));
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
        if(list.length > 50){
            setTimeout(() => {item.className = item.className + " animated zoom-fade-in", item.style.opacity = 1}, (5000/list.length * index));
        } else {
            setTimeout(() => {item.className = item.className + " animated zoom-fade-in", item.style.opacity = 1}, (index * 100));
        }
    })
})();

(function paginatorAnimation(){
    list = [...document.getElementById("paginator").getElementsByTagName("div")];
    list.forEach((item, index) => {
        setTimeout(() => {
            item.className = item.className + " fade-in";
            setTimeout(() => {
                item.style.opacity = 1;
                item.className = item.className.replace("fade-in", "swing-hover");
            }, 1000);
        }, (index * 200));
    })
})();