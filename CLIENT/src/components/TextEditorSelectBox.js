import * as go from 'gojs';

var customEditor = new go.HTMLInfo();

  var customSelectBox = document.createElement("select");

  customEditor.show = function(textBlock, diagram, tool) {
    if (!(textBlock instanceof go.TextBlock)) return;

    // Populate the select box:
    customSelectBox.innerHTML = "";

    var list = textBlock.choices;
    // Perhaps give some default choices if textBlock.choices is null
    if (list === null) list = ["Default A", "Default B", "Default C"];
    var l = list.length;
    for (var i = 0; i < l; i++) {
      var op = document.createElement("option");
      op.text = list[i];
      op.value = list[i];
      if (list[i] === textBlock.text) op.selected = true;
      customSelectBox.add(op, null);

      // consider also adding the current value, if it is not in the choices list
    }

    // After the list is populated, set the value:
    customSelectBox.value = textBlock.text;

    // Do a few different things when a user presses a key
    customSelectBox.addEventListener("keydown", function(e) {
      var key = e.key;
      if (key === "Enter") { // Accept on Enter
        tool.acceptText(go.TextEditingTool.Enter);
        return;
      } else if (key === "Tab") { // Accept on Tab
        tool.acceptText(go.TextEditingTool.Tab);
        e.preventDefault();
        return false;
      } else if (key === "Escape") { // Cancel on Esc
        tool.doCancel();
        if (tool.diagram) tool.diagram.focus();
      }
    }, false);

    var loc = textBlock.getDocumentPoint(go.Spot.TopLeft);
    var pos = diagram.transformDocToView(loc);
    customSelectBox.style.left = pos.x + "px";
    customSelectBox.style.top  = pos.y + "px";
    customSelectBox.style.position = 'absolute';
    customSelectBox.style.zIndex = 100; // place it in front of the Diagram

    if (diagram.div !== null) diagram.div.appendChild(customSelectBox);
    customSelectBox.focus();
  }

  customEditor.hide = function(diagram, tool) {
    try{
      diagram.div.removeChild(customSelectBox);
    }catch(e){
      console.log(e);
    }
  }

  customEditor.valueFunction = function() { return customSelectBox.value; }

const TextEditorSelectBox = customEditor;
export default TextEditorSelectBox;