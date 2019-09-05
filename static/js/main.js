const time = document.getElementById("tempBan") ? Number(document.getElementById("tempBan").getAttribute("delta")) : null;
const days = document.getElementById("days");
const hours = document.getElementById("hours");
const min = document.getElementById("minutes");
const sec = document.getElementById("seconds");

if (Boolean(time)) {
    let timerId = setTimeout(function loop() {
        if (new Date(Date.now()) > new Date(time)) {
            tick();
            timerId = setTimeout(loop, 1000);
        }
    }, 0);
}

function tick() {
    let timer = new Date(new Date(time * 1000) - Date.now());
    if (timer.getDay() === 0) {
        if (days) {
            days.hidden = true;
        }
        if (timer.getHours() === 0) {
            if (hours) {
                hours.hidden = true;
            }
            if (timer.getMinutes() === 0) {
                if (min) {
                    min.hidden = true;
                }
                if (timer.getSeconds() === 0) {
                    if (sec) {
                        sec.hidden = true;
                    }
                }
            }
        }
    }
    if (days) {
        days.getElementsByTagName("span")[0].textContent = timer.getDay();
    }
    if (hours) {
        hours.getElementsByTagName("span")[0].textContent = timer.getHours();
    }
    if (min) {
        min.getElementsByTagName("span")[0].textContent = timer.getMinutes();
    }
    if (sec) {
        sec.getElementsByTagName("span")[0].textContent = timer.getSeconds();
    }
}


function preloaderContinue(event){
    let loader = document.getElementById("loader");
    loader.style.display = "none";
}