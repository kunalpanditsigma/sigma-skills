ObjC.import('Cocoa');
ObjC.import('PDFKit');
function run(argv) {
  var src = argv[0], outDir = argv[1], scale = parseFloat(argv[2] || '1.5');
  var first = argv[3] ? parseInt(argv[3]) : 1;
  var last = argv[4] ? parseInt(argv[4]) : 0;
  var doc = $.PDFDocument.alloc.initWithURL($.NSURL.fileURLWithPath(src));
  var n = doc.pageCount;
  if (!last || last > n) last = n;
  var out = [];
  for (var i = first - 1; i < last; i++) {
    var page = doc.pageAtIndex(i);
    var img = $.NSImage.alloc.initWithData(page.dataRepresentation);
    var sz = img.size;
    var w = Math.round(sz.width * scale), h = Math.round(sz.height * scale);
    var canvas = $.NSImage.alloc.initWithSize({width: w, height: h});
    canvas.lockFocus;
    $.NSColor.whiteColor.setFill;
    $.NSBezierPath.fillRect({origin: {x: 0, y: 0}, size: {width: w, height: h}});
    img.drawInRect({origin: {x: 0, y: 0}, size: {width: w, height: h}});
    canvas.unlockFocus;
    var rep = $.NSBitmapImageRep.imageRepWithData(canvas.TIFFRepresentation);
    var png = rep.representationUsingTypeProperties(4, $.NSDictionary.dictionary);
    var p = outDir + '/p' + String(i + 1).padStart(2, '0') + '.png';
    png.writeToFileAtomically(p, true);
    out.push('p' + (i + 1) + ' ' + w + 'x' + h);
  }
  return 'pages=' + n + ' | ' + out.join(', ');
}
