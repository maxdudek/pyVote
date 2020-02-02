/**
* Runs when sheet is opened
*/
function onOpen() {
  // Try New Google Sheets method
  try{
    var ui = SpreadsheetApp.getUi();
    ui.createMenu('Create Ranked Poll')
    .addItem('Generate Form', 'getCandidatesFromSheet')
    .addToUi();
  }

  // Log the error
  catch (e){Logger.log(e)}

  // Use old Google Spreadsheet method
  finally{
    var items = [
      {name: 'Generate Form', functionName: 'getCandidatesFromSheet'},

    ];
      ss.addMenu('Create Ranked Poll', items);
  }
}

/**
* Gets all candidates from sheet and inputs them into form
*/
function getCandidatesFromSheet() {
  var sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
  var name = sheet.getRange(1, 1).getValue();
  var values = sheet.getRange(2, 1, sheet.getLastRow(), 1).getValues();
  //var r = 2;
  var choices = [];
  var j = 0;
  while(values[j][0] != "") {
    choices[j] = values[j][0];
    j += 1;
  }
  /*for (var i = 1; r >= 1; r--){
    if (values[r][0] != "") break;
  }
  values.splice(r + 1, values.length - r - 1);*/

  var choiceNumbers = [];
  for(var i=1; i<values.length; i++) {

    choiceNumbers[i-1] = getOrdinal(i) + " Choice ";
  }
  createAndSendDocument(name, choices, choiceNumbers);
}

var getOrdinal = function(n) {
  var s=["th","st","nd","rd"],
  v=n%10;
  return n+(s[(v-20)%10]||s[v]||s[0]);
}

/**
 * Creates a Google Doc and sends an email to the current user with a link to the doc.
 */
function createAndSendDocument(name, columnsArr, rowsArr) {
  // Create a new form, then add a checkbox question, a multiple choice question,
  // a page break, then a date question and a grid of questions.
  var form = FormApp.create(name);

  var gridItem = form.addGridItem();
  gridItem.setTitle(name)
      .setColumns(columnsArr)
      .setRows(rowsArr);
      //.setColumns(['Chocolate', 'Vanilla', 'Cookie Dough', 'Chocolate Peanut Butter', 'Strawberry'])
      //.setRows(['1st Choice', '2nd Choice', '3rd Choice', '4th Choice', '5th Choice']);

  var gridItemValidation = FormApp.createGridValidation()
  .setHelpText('Select one item per column.')
  .requireLimitOneResponsePerColumn()
  .build();

  gridItem.setValidation(gridItemValidation);

  Logger.log('Published URL: ' + form.getPublishedUrl());
  Logger.log('Editor URL: ' + form.getEditUrl());

  // Get the URL of the document.
  var url = form.getPublishedUrl();

  // Get the email address of the active user - that's you.
  var email = Session.getActiveUser().getEmail();

  // Get the name of the document to use as an email subject line.
  var subject = 'Your new form';

  // Append a new string to the "url" variable to use as an email body.
  var body = 'Link to your doc: ' + url;

  // Send yourself an email with a link to the document.
  GmailApp.sendEmail(email, subject, body);
}
