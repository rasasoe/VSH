const preview = document.getElementById("preview");
const userContent = new URLSearchParams(window.location.search).get("content");

preview.innerHTML = userContent;
document.write(window.location.hash);
