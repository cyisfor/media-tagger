var prev = document.querySelector("link[rel=prev]");
var next = document.querySelector("link[rel=next]");
/* keydown, because otherwise we hit alt-left to go back, and then let go,
	 which makes a keyup, which goes back again.
*/
function toggle_keycodes() {
	function react(ev) {
		if((!ev.ctrlKey) || ev.shiftKey || ev.altKey || ev.metaKey) return;
		switch(ev.keyCode) {
		case 37: // left
			document.location = prev.href;
			break;
		case 38: // up
			document.location = "..";
			break;
		case 39: // right
			document.location = next.href;
			break;
		default:
			return;
		}
		ev.preventDefault();
	}

	function showcodes(ev) {
		console.log("Key pressed:",ev);
	}

	var reacting = true;
	document.addEventListener('keydown',function (ev) {
		if(reacting) return react(ev);
		return showcodes(ev);
	},true);
	return function() {
		reacting = !reacting;
	}
}

toggle_keycodes = toggle_keycodes();
