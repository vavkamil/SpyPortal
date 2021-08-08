<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Captive Spy Portal</title>

  <script>
    function initFingerprintJS() {
      // Initialize an agent at application startup.
      const fpPromise = FingerprintJS.load()

      // Get the visitor identifier when you need it.
      fpPromise
        .then(fp => fp.get())
        .then(result => {
          // This is the visitor identifier:
          const visitorId = result.visitorId;
          //console.log(navigator);
          document.getElementById("user-agent").textContent = navigator.userAgent;
          document.getElementById("screen-resolution").textContent = result.components.screenResolution.value;
          document.getElementById("timezone").textContent = result.components.timezone.value;
          document.getElementById("locale").textContent = result.components.languages.value[0];

          // document.getElementById("textarea").innerHTML = JSON.stringify(navigator);
        })
    }
  </script>
  <script async src="fp.min.js" onload="initFingerprintJS()"></script>
</head>
<body>
  <h1>Captive Spy Portal</h1>
  <h2>Proof of Concept</h2>
  <hr>

  <h3>Connected client info</h3>

<?php

$ipAddress = $_SERVER['REMOTE_ADDR'];
$macAddr = false;

#run the external command, break output into lines
$arp = `arp -a $ipAddress`;
$lines = explode("\n", $arp);

#look for the output line describing our IP address
foreach($lines as $line) {
  $cols = preg_split('/\s+/', trim($line));
  $cols_ip = str_replace( array("(", ")"), "", $cols[1]);

  if ($cols_ip == $ipAddress) {
    $macAddr = $cols[3];
  }
}

$vendor = "?";

$handle = fopen("macaddress.io-db.json", "r");
  if ($handle) {
    while (($line = fgets($handle)) !== false) {
      $macaddress = json_decode($line, true);

      if(strtoupper(substr($macAddr, 0, 8)) == $macaddress["oui"]) {
        $vendor = $macaddress["companyName"];
      }
    }

    fclose($handle);
  } else {
    // error opening the file
}

echo "<p>IP address: <strong>",$ipAddress,"</strong></p>";
echo "<p>MAC: <strong>",strtoupper($macAddr),"</strong></p>";
echo "<p>Vendor: <strong>",$vendor,"</strong></p>";


ini_set('display_errors', 1);
ini_set('display_startup_errors', 1);
error_reporting(E_ALL);

echo "<h3>Saved SSID networks</h3>";

$dir = 'sqlite:/home/pi/SpyPortal/output_probe_data.db';
$dbh  = new PDO($dir) or die("cannot open the database");
$sth = $dbh->prepare("SELECT ssid FROM probe_requests WHERE client = ?");
$sth->execute(array(strtoupper($macAddr)));
$red = $sth->fetchAll();
$saved_networks = "";
foreach ($red as $lol) {
  $saved_networks .= $lol[0] . ", ";
}
echo "<p>SSID: <strong>",$saved_networks,"</strong></p>";

//foreach ($dbh->query($query) as $row) {
//  echo $row[0];
//}
$dbh = null; //This is how you close a PDO connection

?>

  <h3>JavaScript Browser Information</h3>

  <p>User-Agent: <strong><span id="user-agent"></span></strong></p>
  <p>Screen Resolution: <strong><span id="screen-resolution"></span></strong></p>
  <p>Timezone: <strong><span id="timezone"></span></strong></p>
  <p>Locale: <strong><span id="locale"></span></strong></p>

  <p>Installed applications (TODO - schemeflood.com): <strong><span id="schemeflood"></span></strong></p>
  <!-- <button onclick="myFunction()">Try it</button> -->

  <!-- <textarea id="textarea" style="height: 500px;width:1000px;"></textarea> -->

  <p>Installed extensions (Chrome):</p>

  <script>
    let extensions = [
        ["1Password", "chrome-extension://aeblfdkhhhdcdjpifhhbdiojplfjncoa/images/icons/onepassword-48.png"],
        ["LastPass", "chrome-extension://hdokiejnpimakedhajhdlcegeplioahd/images/icon48.png"],
        ["Dashlane", "chrome-extension://fdjamakpfbbddfjaooikfcpapjohcfmg/content/injected/logo-autofill-known.svg"],
        ["Ghostery", "chrome-extension://mlomiejdfkolichcflejclcbmpeaniij/app/images/icon48.png"],
    ];

    var detect = function(name, base) {
        var s = document.createElement('img');
        s.style.width = "50px";
        s.style.height = "50px";
        s.id = name;
        s.onerror = function() {s.style.display = "none";};
        document.body.appendChild(s);
        s.src = base;
    }

    if(navigator.userAgent.includes("Chrome")) {
      extensions.forEach(extension => {
        //alert(extension[0]);
        detect(extension[0], extension[1]);
      });
    }



  </script>
</body>
</html>
