import logging
import boto3
from strands import Agent
from strands.models import BedrockModel
from strands.models.openai import OpenAIModel
from flask import Flask, request, render_template_string, Response
import io
import os
import sys
import re
import glob
from contextlib import redirect_stdout
from inspect import signature # Needed to inspect pytho parameter types

logger = logging.getLogger("rjAIagent")

app = Flask(__name__, static_url_path='')

# HTML template with placeholders
template_html = """
<!doctype html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>🤖 Agentic AI Demo Lab</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background-color: #f9f9f9;
            padding: 0px;
        }
        .banner {
            background-color: #222; /* Dark background */
            color: #f1f1f1;          /* Light text */
            padding: 20px;
            text-align: center;
        }
        .banner h1 {
            margin: 5px 0;
            font-size: 1.5em;
        }
        iframe {
            width: 80%;
            height: 1200px;
            border: 2px solid #ccc;
            border-radius: 8px;
        }
        #jsonSource, #prettyOutput, #outputrsp {
            padding: 10px;
            border: 1px solid #ccc;
            background-color: #eee;
            border-radius: 5px;
            margin-top: 10px;
            white-space: pre-wrap;
        }
        .banner p {
            margin: 0;
            font-size: 1em;
        }

        .content {
            padding: 10px;
        }

        .form-group {
            margin-bottom: 5px;
        }

        .resizable-iframe {
            resize: both;
            overflow: auto;
            border: 2px solid #aaa;
            width: 80%;
            height: 600px;
            margin-top: 30px;
        }

        label {
            display: inline-block;
            width: 150px;
            font-weight: bold;
            vertical-align: middle;
        }

        input[type="text"], select {
            width: 300px;
            padding: 8px;
            font-size: 1em;
        }

        textarea {
            font-family: roboto;
            font-size: 16px;
        }

        button[type="submit"] {
            padding: 12px 24px;
            font-size: 18px;
            font-weight: bold;
            width: 200px;       /* Optional: fixed width */
            height: 50px;       /* Optional: fixed height */
            cursor: pointer;
        }

    </style>
</head>
<body>

<div class="banner">
    <h1>Dynamic Dashboards App (AccuKnox)</h1>
    <p>Powered by Agentic AI</p>
</div>

<div class="content">
<form method="POST" id="inputForm">

  <div class="form-group">
      <label for="textInput">Input Prompt:</label>
      <textarea id="inprompt" name="input_string" rows="5" cols="120" placeholder="type prompt here..." required></textarea><br><br>
  </div>

  <div class="form-group">
      <label>Select LLM:</label>
      <select id="modelsel" name="model_select">
        <option value="us.deepseek.r1-v1:0">Deep Seek r1-v1</option>
        <option value="us.anthropic.claude-3-7-sonnet-20250219-v1:0">Anthropic Claude 3.7 Sonnet</option>
        <option value="gpt-4o">OpenAI GPT 4o</option>
      </select>
  </div><br>

    <div class="form-group">
      <label for="textInput">Credentials</label>
      <textarea hidden="" id="creds" name="creds" rows="5" cols="120" placeholder="aws_access_key_id = XXX\naws_secret_access_key = YYY\nregion = us-east-1" required></textarea><br><br>
      <input type="checkbox" onclick="myFunction()">Show Credentials
    </div>

  <br>
  <button type="submit">Submit</button>
</form>
</div>

{% if graphfn %}
<div class="resizable-iframe">
<iframe src="{{ graphfn }}" title="Embedded HTML Page"></iframe>
</div>
{% endif %}

{% if output %}
<h2>Output:</h2>
<pre id="outputrsp">{{ output }}</pre>
{% endif %}

{% if processed %}
<h3>Full Response with metadata:</h3>
<div id="jsonSource" style="display: none;">
    {{ processed }}
</div>
<div id="prettyOutput"></div>
{% endif %}

<script>
function myFunction() {
  var x = document.getElementById("creds");
  if (x.hasAttribute("hidden")) {
    x.removeAttribute("hidden");
  } else {
    x.setAttribute("hidden", "");
  }
}
</script>
<script src="https://cdn.jsdelivr.net/npm/json5@2.2.3/dist/index.min.js"></script>
<script>
window.onload = function () {
    const input = document.getElementById("jsonSource").textContent.trim();
    const output = document.getElementById("prettyOutput");

    try {
        const obj = JSON5.parse(input);
        const pretty = JSON.stringify(obj, null, 4);
        output.textContent = pretty;
    } catch (e) {
        output.textContent = "Invalid JSON: " + e.message;
    }
};

</script>

  <script>
    // Centralized field name definitions
    const fields = {
      textInput: 'inprompt',
      dropdown: 'modelsel',
      textInput2: 'creds'
    };

    // Load stored values
    window.onload = function () {
      for (let key in fields) {
        const savedValue = localStorage.getItem(fields[key]);
        if (savedValue) {
          document.getElementById(fields[key]).value = savedValue;
        }
      }
    };

    // Save values on form submit
    document.getElementById('inputForm').addEventListener('submit', function (event) {
      for (let key in fields) {
        const value = document.getElementById(fields[key]).value;
        localStorage.setItem(fields[key], value);
      }
    });
  </script>

</body>
</html>
"""

def text_to_dict(multiline_text, delimiter="="):
    result = {}
    lines = multiline_text.strip().split("\n")
    for line in lines:
        if delimiter in line:
            key, value = line.split(delimiter, 1)
            result[key.strip()] = value.strip()
    return result

def agentProcess(prompt: dict, modelsel: str, creds: str):
    temperature=0.3
    cred_dict = text_to_dict(creds)
    if "aws_access" in creds:
        # Create a BedrockModel
        session = boto3.Session(
            aws_access_key_id=cred_dict['aws_access_key_id'],
            aws_secret_access_key=cred_dict['aws_secret_access_key'],
            region_name=cred_dict['region'],
        )
        amodel = BedrockModel(
            model_id=modelsel,
            temperature=temperature,
            boto_session=session,
        )
    else:
        amodel = OpenAIModel(
            client_args={
                "api_key": cred_dict['openai_key'],
            },
            # **model_config
            model_id="gpt-4o",
            params={
                "max_tokens": 1000,
                "temperature": temperature,
            }
        )
    # Start agent
    agent = Agent(
        model=amodel
    )
    return agent(prompt)

def processGeneratedCode(intext: str):
    fenced_pattern = re.compile(r'```python(?:[\w+-]*)\n(.*?)```', re.DOTALL)
    code_blocks = fenced_pattern.findall(intext)[0]
    updated_code = re.sub(r'\bfig\.show\(\)', r"fig.write_html('line_plot.html')", code_blocks)
    f = open('/tmp/agentai.py', 'w')
    f.write(updated_code)
    f.close()

@app.route("/", methods=["GET", "POST"])
def index():
    processed = None
    output = None
    user_input = None
    buffer = io.StringIO()
    if request.method == "POST":
        with redirect_stdout(buffer):
           user_input = request.form["input_string"]
           modelsel = request.form.get('model_select', '')
           creds = request.form.get('creds', '')
           result = agentProcess(prompt=user_input, modelsel=modelsel, creds=creds)
           processed = result.message
        output = buffer.getvalue()
        processGeneratedCode(intext=output)
        return render_template_string(template_html, processed=processed, output=output, graphfn="/graph")

    return render_template_string(template_html, processed=None, output=None, user_input=None, graphfn=None)

@app.route("/graph", methods=["GET"])
def server_graph():
    os.system(". /sandbox/bin/activate && sandbox_python3.12 -u /tmp/agentai.py")
    list_of_files = glob.glob('./*.html') # * means all if need specific format then *.csv
    if not list_of_files:
        return Response("No graph html generated. Please prompt to add an html file...", mimetype='text/html')
    latest_file = max(list_of_files, key=os.path.getctime)
    with open(latest_file, "r", encoding="utf-8") as f:
        html_content = f.read()
    os.remove(latest_file) # Remove the graph html file
    return Response(html_content, mimetype='text/html')

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', use_reloader=True)

