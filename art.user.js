// ==UserScript==
// @name        explanation coordinate finder
// @namespace   utilities
// @description finds uh yeah
// @downloadURL http://[fcd9:e703:498e:5d07:e5fc:d525:80a6:a51c]/stuff/code/image/tagger/art.user.js
// @include     http://[fcd9:e703:498e:5d07:e5fc:d525:80a6:a51c]/art/~page/*
// @version     1
// @grant       none
// ==/UserScript==

function round(f) {
	return Math.round(f*100)/100.0;
}

document.addEventListener('DOMContentLoaded',function() {
	var status = document.createElement('div');
	status.content = document.createTextNode('status');
	status.appendChild(status.content);
	status.style.display = 'none';
	status.style.backgroundColor='#f22';
	status.style.position = 'absolute';
	status.style.top = '1%';
	status.style.left = '1%';
	var selection = document.createElement('div');
	selection.style.display = 'none';
	selection.style.border = 'thin solid black';
	selection.style.backgroundColor = 'rgba(255,255,255,0.3)';
	selection.style.position = 'absolute';
	var popup = document.createElement('div');
	popup.style.display = 'none';
	popup.style.backgroundColor = 'white';

	var img = document.getElementById('img');
	function toPercent(n,d) {
		return Math.round(n*10000/d)/100.0 + '%';
	}
	document.body.appendChild(status);
	document.body.appendChild(popup);
	img.appendChild(selection);
	var save = {};
	img.addEventListener('click',function(e) {
		e.preventDefault();
		if(selection.finished) {
			selection.style.display = 'none';
			selection.finished = false;
			status.style.backgroundColor = '#f22';
			popup.style.display = 'none';
			return;
		}
		var x = e.clientX - img.offsetLeft;
		var y = e.clientY - img.offsetTop;

		if(!selection.started) {
			status.style.backgroundColor = '#ff2';
			selection.started = true;
			selection.left = x;
			selection.top = y;
			selection.style.left = toPercent(x,img.clientWidth);
			selection.style.top = toPercent(y,img.clientHeight);
		} else {
			status.style.backgroundColor = '#2f2';
			selection.finished = true;
			selection.started = false;
			var w = x - selection.left;
			var h = y - selection.top;
			selection.style.width = toPercent(w,img.clientWidth);
			selection.style.height = toPercent(h,img.clientHeight);
			selection.style.display = 'block';
			popup.style.position = 'fixed';
			popup.style.left = '25%';
			popup.style.top = '25%';
			while(popup.firstChild) {
				popup.removeChild(popup.firstChild);
			}
			function p() {
				var e = document.createElement('p');
				var s = '';
				for(var i=0;i<arguments.length;++i) {
					s += arguments[i];
				}
				e.appendChild(document.createTextNode(s));
				popup.appendChild(e);
			}
			function q(s) {
				return "'"+s+"', ";
			}
			p("UPDATE explanations SET ",
			  "top = '",selection.style.top,"',",
			  "derpleft = '",selection.style.left,"',",
			  "w = '",selection.style.width,"',",
			  "h = '",selection.style.height,"' ",
			  "WHERE id = ");
			var a = document.location.pathname.split('/');
			p("INSERT INTO explanations (image,top,derpleft,w,h,script)",
			  "VALUES (x'",a[a.length-2],"'::int,",
			  q(selection.style.top),
			  q(selection.style.left),
			  q(selection.style.width),
			  q(selection.style.height),
			  "'");
			popup.style.display = 'block';
		}
	},true);

	popup.addEventListener('click',function(e) {
		if(!e.ctrlKey) return;
		popup.style.display = 'none';
	},false);
	img.addEventListener('mousemove',function(e) {
		status.style.display = 'inline';
		var left = (e.clientX-img.offsetLeft);
		var top = (e.clientY-img.offsetTop);
		var w = img.clientWidth;
		var h = img.clientHeight;
		if(save.left) {
			status.content.nodeValue = "top = '"+toPercent(save.top,h)+"', "+
				"derpleft = '"+toPercent(save.left,w)+"', "+
				"w = '"+toPercent(left-save.left,w)+"', h = '"+toPercent(top-save.top,h)+"'";
		} else {
			status.content.nodeValue = '('+toPercent(top,h)+','+toPercent(left,w)+')';
		}
	},false);
},true);
