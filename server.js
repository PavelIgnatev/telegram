const express = require("express");
const bodyParser = require("body-parser");
const Docker = require("dockerode");

const app = express();
const port = 3000;

app.use(bodyParser.json());

const docker = new Docker();

app.post("/start_agent", async (req, res) => {
  try {
    const agentName = `agent_${Date.now()}`;
    const { urls } = req.body;

    // Dockerfile content
    const dockerfileContent = `
      FROM python:3
      WORKDIR /app
      RUN apt-get update && apt-get install -y git
      RUN git clone https://github.com/PavelIgnatev/agent /app
    `;

    const fs = require("fs");
    const dockerfilePath = `/tmp/Dockerfile_${agentName}`;
    fs.writeFileSync(dockerfilePath, dockerfileContent);

    const container = await docker.createContainer({
      name: agentName,
      Image: "python:3",
      Tty: true,
      OpenStdin: true,
      HostConfig: {
        Binds: [`${dockerfilePath}:/Dockerfile`],
      },
      Cmd: [
        "sh",
        "-c",
        `apt-get update && apt-get install -y git && git clone https://github.com/PavelIgnatev/agent /app && python3 -m venv myenv && pip install --upgrade pip && pip install --no-cache-dir -r app/requirements.txt && python3 app/chat_parser.py --urls ${urls.join(
          " "
        )}`,
      ],
    });
    await container.start();
    fs.unlinkSync(dockerfilePath);

    res.json({ success: true, agentName });
  } catch (error) {
    console.error("Error starting agent:", error.message);
    res.status(500).json({ success: false, error: error.message });
  }
});

app.get("/check_status/:agentName", async (req, res) => {
  try {
    const agentName = req.params.agentName;

    const container = docker.getContainer(agentName);
    const data = await container.inspect();

    res.json({ success: true, status: data.State.Status });
  } catch (error) {
    console.error("Error checking agent status:", error.message);
    res.status(500).json({ success: false, error: error.message });
  }
});

app.listen(port, () => {
  console.log(`Server is running on port ${port}`);
});
