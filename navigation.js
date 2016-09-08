var prev = document.querySelector("link[rel=prev]");
var next = document.querySelector("link[rel=next]");

document.addEventListener('keyup', function(ev) {
	switch(ev.keyCode) {
		case 37: // left
		document.location = prev.href;
		ev.preventDefault();
		break;
		case 39: // right
		document.location = next.href;
		ev.preventDefault();
		break;
	}
},true);
