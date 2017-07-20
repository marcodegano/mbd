//Returns random RGB values.
function randomColor() {
        
  rgb = Math.floor((Math.random() * 255) + 1);
        
  return rgb;
}

//Returns a random number from 1 to the maximum.
function setRandom(maxNum) {
        
  var rndNum = Math.floor((Math.random() * maxNum) + 1);

  return rndNum;
}

//Erases the canvas specified.
function eraseCanvas(can) {
  var ctx = can.getContext("2d");
        
  ctx.clearRect(0, 0, can.width += 0, can.height += 0);
}