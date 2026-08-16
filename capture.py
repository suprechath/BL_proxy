import json
import urllib.request
from mitmproxy import http

def request(flow: http.HTTPFlow):
    url = flow.request.pretty_url
    
    if "ValidateToUpdateInstruction" in url:
        print("\n--- 🎯 CAUGHT REQUEST: UpdateInstruction ---")
        payload = flow.request.get_text()
        with open("validate_instruction.log", "a") as log_file:
            log_file.write(f"URL: {url}\n")
            log_file.write(f"Payload: {payload}\n")
            log_file.write("-" * 100 + "\n")
        
    elif "AddInstructionException" in url:
        payload = flow.request.get_text()
        
        # Parse the JSON payload so we can easily check and extract values
        try:
            data = json.loads(payload)
            
            # Check if ExceptionLevel is "4" inside the parsed JSON
            if str(data.get("ExceptionLevel")) == "1":
                print("\n--- 🎯 CAUGHT REQUEST: Exception Level 1 (High) ---")
                
                # Extract variables (using .get() prevents errors if the key is missing)
                batch_id = str(data.get("BatchId", ""))
                phase_number = str(data.get("PhaseNumber", ""))
                step_number = str(data.get("StepNumber", ""))
                instruction_number = str(data.get("InstructionNumber", ""))
                
                # Concatenate your custom strings
                batch_link = "https://demo.bl-client.com/Batch/BatchProcess?BatchId=" + batch_id
                psi_combo = "{" + phase_number + ":" + step_number + ":" + instruction_number + "}"
                
                # Write everything to exception.log
                with open("exception.log", "a") as log_file:
                    log_file.write(f"URL: {url}\n")
                    log_file.write(f"Batch Link: {batch_link}\n")
                    log_file.write(f"Phase/Step/Instruction: {psi_combo}\n")
                    log_file.write("-" * 100 + "\n")
                
                # ---------------------------------------------------------
                # 3. Push to Make.com Webhook
                # ---------------------------------------------------------
                webhook_url = "https://hook.us2.make.com/17l9i61f2eco7qga8uy12i1tm7o9kgcp"
                
                # Create the Python dictionary (equivalent to your JS object)
                webhook_data = {
                    "alert": "Critical Exception Interruption",
                    "batchId": batch_link,
                    "parameter": psi_combo
                }
                
                # Convert dictionary to a JSON string and encode it to bytes (equivalent to JSON.stringify)
                json_bytes = json.dumps(webhook_data).encode('utf-8')
                
                # Prepare and send the POST request
                req = urllib.request.Request(webhook_url, method="POST")
                req.add_header('Content-Type', 'application/json')
                
                proxy_handler = urllib.request.ProxyHandler({}) 
                opener = urllib.request.build_opener(proxy_handler)
                
                try:
                    # Send it using the custom opener instead of the default urlopen
                    opener.open(req, data=json_bytes, timeout=5)
                    print("🚀 Webhook successfully sent to Make.com directly!")
                except Exception as e:
                    print(f"⚠️ Failed to send webhook: {e}")
                    
        except json.JSONDecodeError:
            # If the payload happens to not be valid JSON, just ignore it and move on
            pass