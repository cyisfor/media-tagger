function reload_later(dest,src) {
	var img = document.createElement('img');
	function setsrc() {
		img.style.height = '219px';
		img.src = src;
	}
	img.addEventListener('error', function(e) {
		setTimeout(setsrc,1000);
	},false);
	img.addEventListener('load',function() {
		dest.parentNode.replaceChild(img,dest);
	},false);
	setsrc()
}
