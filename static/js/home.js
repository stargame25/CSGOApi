(function contentAnimation(){
    content = [...document.getElementById("content").children];
    content.forEach((item, index) => {
        setTimeout(() => {item.className = item.className + " animated zoomFadeIn", item.style.opacity = 1}, index*200);
    })
})();