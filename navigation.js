var prev = document.querySelector("link[rel=prev]");
var next = document.querySelector("link[rel=next]");

document.addEventListener('keydown'function(ev) {
	switch(ev.keyCode) {
		case 37: // left
		document.location = prev.href;
		break;
		case 39: // right
		document.location = next.href;
	}
}
