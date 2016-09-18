var prev = document.querySelector("link[rel=prev]");
var next = document.querySelector("link[rel=next]");

/* keydown, because otherwise we hit alt-left to go back, and then let go,
	 which makes a keyup, which goes back again.
*/
function toggle_keycodes() {
	function react(ev) {
		if(ev.ctrlKey || ev.shiftKey || ev.altKey || ev.metaKey) return;
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
	}

	function showcodes(ev) {
		console.log("Key pressed:",ev);
	}

	var reacting = false;
	function toggle() {
		reacting = !reacting;
		document.removeEventListener('keydown',listener,true);
		listener = document.addEventListener('keydown',reacting ? react : showcodes,true);
	}
	toggle()
	return toggle;
}
