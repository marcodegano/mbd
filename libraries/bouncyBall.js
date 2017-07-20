var bouncyBall = {
  r: 0,
  g: 0,
  b: 0,
  ySpeed: 0,
  xSpeed: 0,
  ray: 15,
  xPos: 0,
  yPos: 0,
  
  setColor : function() {
    r = randomColor();
    g = randomColor();
    b = randomColor();
  }
};