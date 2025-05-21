import logging
from strands import Agent
from strands.models import BedrockModel
from flask import Flask, request, render_template_string, Response
import io
import os
import sys
import re
import glob
from contextlib import redirect_stdout
from inspect import signature # Needed to inspect pytho parameter types

logger = logging.getLogger("my_agent")

app = Flask(__name__, static_url_path='')

# HTML template with placeholders
template_html = """
<!doctype html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>🤖 Dynamic Dashboards with Agentic AI</title>
    <style>
        body {
            font-family: monospace;
            background-color: #f9f9f9;
            padding: 20px;
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
    </style>
</head>
<body>

<h2>Dynamic Dashboards: Agentic AI Demo</h2>
<form method="POST">
  <div class="form-row">
      <label for="textInput">Input Prompt:</label>
      <textarea name="input_string" rows="5" cols="120" placeholder="type prompt here..." required></textarea><br><br>
  </div>

  <div class="form-row">
      <label>Select LLM:</label>
      <select name="model_select">
        <option value="us.deepseek.r1-v1:0">Deep Seek r1-v1</option>
        <option value="us.anthropic.claude-3-7-sonnet-20250219-v1:0">Anthropic Claude 3.7 Sonnet</option>
      </select>
  </div><br>

  <input type="submit" value="Submit">
</form>

{% if user_input %}
<h2>User Input Prompt:</h2>
<pre>{{ user_input }}</pre>
{% endif %}

{% if graphfn %}
<iframe src="{{ graphfn }}" title="Embedded HTML Page"></iframe>
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
</body>
</html>
"""

def agentProcess(prompt: dict, modelsel: str):
    # Create a BedrockModel
    bedrock_model = BedrockModel(
        model_id=modelsel,
        region_name='us-east-1',
        temperature=0.3,
    )
    # Create an agent with the callback handler
    agent = Agent(
        model=bedrock_model
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
           result = agentProcess(prompt=user_input, modelsel=modelsel)
           processed = result.message
        output = buffer.getvalue()
        processGeneratedCode(intext=output)
        return render_template_string(template_html, processed=processed, output=output, user_input=user_input, graphfn="/graph")

    return render_template_string(template_html, processed=None, output=None, user_input=None, graphfn=None)

@app.route("/graph", methods=["GET"])
def server_graph():
    os.system("python -u /tmp/agentai.py")
    list_of_files = glob.glob('./*.html') # * means all if need specific format then *.csv
    if not list_of_files:
        return Response("No graph html generated. Please prompt to add an html file...", mimetype='text/html')
    latest_file = max(list_of_files, key=os.path.getctime)
    with open(latest_file, "r", encoding="utf-8") as f:
        html_content = f.read()
    os.remove(latest_file) # Remove the graph html file
    return Response(html_content, mimetype='text/html')

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', use_reloader=False)

