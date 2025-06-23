function sendEmails() {
  /*
      - Parameters:
          - None 

      - Return: 
          - None

      - Description:
          - Send emails to the recipients in the Google Sheet.
          - Rotate through the aliases to send emails.
          - Update the status of the email in the Google Sheet.
          - Stop processing if an empty row is found.
  */
  var id = SpreadsheetApp.getActiveSpreadsheet().getId();
  var sheet = SpreadsheetApp.openById(id).getActiveSheet();
  var data = sheet.getDataRange().getValues();

  var aliases = GmailApp.getAliases(); // Get all aliases
  if (aliases.length === 0) {
    Logger.log("No aliases available.");
    return;
  }

  var aliasCount = aliases.length;

  for (var i = 1; i < data.length; i++) {
    var row = data[i];
    var email = row[0];
    var subject = row[1];
    var emailContent = row[2];

    // Stop the loop if required data is missing
    if (!email || !subject || !emailContent) {
      Logger.log("Stopping process due to missing data at row: " + (i + 1));
      break;
    }

    var openTrackingCell = sheet.getRange(i + 1, 5); // Open Email Tracking
    var lastSentCell = sheet.getRange(i + 1, 4);     // Last Sent
    var openAmountCell = sheet.getRange(i + 1, 7);   // Open Amount Column
    var sentTimestampCell = sheet.getRange(i + 1, 8); // Sent Timestamp Column

    // Rotate through aliases
    var aliasToUse = aliases[i % aliasCount];

    var trackingPixelUrl = `[Your app script deploved web app link]?email=${encodeURIComponent(email)}`;

    var emailBody = emailContent + 
      `<img src="${trackingPixelUrl}" width="1" height="1" style="opacity:0; visibility:hidden;">`;

    if (MailApp.getRemainingDailyQuota() > 0) {
      try {
        GmailApp.sendEmail(email, subject, '', {
          htmlBody: emailBody,
          from: aliasToUse,  
          name: 'Company name'
        });

        // Set the initial status as "Sent"
        openTrackingCell.setValue("Sent");
        lastSentCell.setValue(new Date());
        
        // Set the sent timestamp
        sentTimestampCell.setValue(new Date());

        openAmountCell.setValue(""); 

        Logger.log("Email sent successfully to: " + email + " from: " + aliasToUse);
        
        // Wait for 2 seconds before sending the next email (in milliseconds)
        Utilities.sleep(2000); 
      } catch (error) {
        Logger.log("Error sending email to " + email + ": " + error.message);
        openTrackingCell.setValue("Failed");
      }
    } else {
      Logger.log("Daily quota exceeded.");
      break;
    }
  }
}

function doGet(e) {
  /*
      - Parameters:
          - e: Object containing the GET request parameters.

      - Return:
          - ContentService: Tracking pixel image.

      - Description:
          - Handle the GET request to the tracking pixel URL.
          - Update the email status to "Opened" in the Google Sheet.
  */
  if (!e || !e.parameter || !e.parameter.email) {
    Logger.log("No parameters found in GET request.");
    return ContentService.createTextOutput("Error: Missing parameters.");
  }

  var emailToTrack = decodeURIComponent(e.parameter.email);  // Proper decoding

  var userAgent = e.parameter['User-Agent'] || 'Unknown';
  var referer = e.parameter['Referer'] || 'Unknown';

  Logger.log('Request received for email: ' + emailToTrack + ', User-Agent: ' + userAgent + ', Referer: ' + referer);

  var id = SpreadsheetApp.getActiveSpreadsheet().getId();
  var sheet = SpreadsheetApp.openById(id).getActiveSheet();
  var data = sheet.getDataRange().getValues();

  var emailIndex = 0;
  var sentTimestampIndex = 7; 
  var openTrackingIndex = 4;
  var openAmountIndex = 6;
  var lastOpenIndex = 5;

  for (var i = 1; i < data.length; i++) {
    var row = data[i];
    var email = row[emailIndex];

    if (email === emailToTrack) {
      var sentTimestamp = row[sentTimestampIndex];
      
      if (sentTimestamp) {
        var now = new Date();
        var diff = (now - sentTimestamp) / 1000; 

        if (diff < 10) {
          Logger.log("Skipping first request for email: " + emailToTrack);
          return ContentService.createTextOutput("");  
        }

        updateEmailStatus(emailToTrack);
        break;
      }
    }
  }

  var pixel = Utilities.newBlob(
    '\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\xFF\xFF\xFF\xFF\xFF\xFF\x21\xF9\x04\x01\x00\x00\x00\x00\x2C\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x4C\x01\x00\x3B',
    'image/gif'
  );
  return ContentService.createBinaryOutput(pixel).setMimeType(ContentService.MimeType.GIF);
}

function updateEmailStatus(emailToTrack) {
  /*
      - Parameters:
          - emailToTrack: Email address to track.

      - Return:
          - None

      - Description:  
          - Update the email status to "Opened" in the Google Sheet.
          - Update the open count and last open timestamp.
  */
  var id = SpreadsheetApp.getActiveSpreadsheet().getId();
  var sheet = SpreadsheetApp.openById(id).getActiveSheet();
  var data = sheet.getDataRange().getValues();

  var emailIndex = 0;
  var openTrackingIndex = 4;
  var openAmountIndex = 6;
  var lastOpenIndex = 5;

  for (var i = 1; i < data.length; i++) {
    var row = data[i];
    var email = row[emailIndex];

    if (email === emailToTrack) {
      var currentOpenCount = parseInt(row[openAmountIndex]) || 0;
      var newOpenCount = currentOpenCount + 1;

      sheet.getRange(i + 1, openTrackingIndex + 1).setValue("Opened");
      sheet.getRange(i + 1, openAmountIndex + 1).setValue(newOpenCount);

      var formattedDate = Utilities.formatDate(new Date(), Session.getScriptTimeZone(), "yyyy-MM-dd HH:mm:ss");
      sheet.getRange(i + 1, lastOpenIndex + 1).setValue(formattedDate);

      Logger.log("Updated email status and open count for: " + emailToTrack);
      break;
    }
  }
}