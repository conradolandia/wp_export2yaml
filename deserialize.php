<?php
// deserialize_php.php
// Reads a PHP serialized string from STDIN, unserializes it, and outputs JSON to STDOUT.
// Handles potential errors during unserialization.

// Ensure error reporting is minimal to not pollute STDOUT unless we want it
error_reporting(0);
ini_set('display_errors', 0);

// Read from stdin and ensure we have a string
$serialized_data = trim(file_get_contents('php://stdin'));

if ($serialized_data === false || $serialized_data === '') {
    // Error reading from stdin or empty input
    $output = ['error' => 'Failed to read from STDIN or empty input.'];
    echo json_encode($output);
    exit(1);
}

// Attempt to unserialize the data
// Use a custom error handler to catch warnings/errors from unserialize()
$unserialized_value = false;
$error_during_unserialize = null;

set_error_handler(function($errno, $errstr) use (&$error_during_unserialize) {
    $error_during_unserialize = $errstr;
    return true; // Prevent default PHP error handling
}, E_WARNING); // Catch warnings from unserialize()

$unserialized_value = @unserialize($serialized_data);

restore_error_handler(); // Restore original error handler

if ($unserialized_value === false && $serialized_data !== 'b:0;' && $error_during_unserialize !== null) {
    // Unserialize failed (and it's not the boolean false 'b:0;')
    $output = [
        'error' => 'Unserialization failed.',
        'message' => $error_during_unserialize,
        'raw_input' => $serialized_data
    ];
    echo json_encode($output);
    exit(1);
} else {
    // Unserialization succeeded (or it was the boolean false)
    // Encode the result to JSON for easy parsing in Python
    $json_output = json_encode($unserialized_value, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
    
    if ($json_output === false) {
        // Error encoding to JSON
         $output = [
            'error' => 'Failed to encode result to JSON.',
            'message' => json_last_error_msg(),
            'unserialized_value' => $unserialized_value
        ];
        echo json_encode($output);
        exit(1);
    }

    echo $json_output;
    exit(0);
}

?>
