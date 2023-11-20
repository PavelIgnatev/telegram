const fs = require("fs");
const { readdir, unlink } = require("fs").promises;
const Docker = require("dockerode");
const express = require("express");

const path = require("path");
const { execSync } = require("child_process");

const docker = new Docker();
const router = express.Router();

/**
 * @swagger
 * /agent:
 *   post:
 *     summary: Создание нового агента
 *     security: []
 *     tags:
 *       - Agent
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             properties:
 *               urls:
 *                 type: array
 *                 items:
 *                   type: string
 *     responses:
 *       '200':
 *         description: Success
 *         content:
 *           application/json:
 *             example:
 *               success: true
 *               data:
 *                 agentName: agent_123456789
 *       '500':
 *         description: Error
 *         content:
 *           application/json:
 *             example:
 *               success: false
 *               error: Error message here
 */
/**
 * @swagger
 * /agents:
 *   get:
 *     summary: Получение списка всех агентов
 *     tags:
 *       - Agent
 *     security: []
 *     responses:
 *       '200':
 *         description: Success
 *         content:
 *           application/json:
 *             example:
 *               success: true
 *               data:
 *                 agents:
 *                   - agentName: agent_123456789
 *                     createdAt: "2023-11-20T12:00:00Z"
 *                     status: "running"
 *                   - agentName: agent_987654321
 *                     createdAt: "2023-11-19T15:30:00Z"
 *                     status: "stopped"
 *       '500':
 *         description: Error
 *         content:
 *           application/json:
 *             example:
 *               success: false
 *               error: Error message here
 */
/**
 * @swagger
 * /agents/{agentName}:
 *   get:
 *     summary: Получение информации об агенте по его имени
 *     tags:
 *       - Agent
 *     parameters:
 *       - in: path
 *         name: agentName
 *         required: true
 *         schema:
 *           type: string
 *     security: []
 *     responses:
 *       '200':
 *         description: Success
 *         content:
 *           application/json:
 *             example:
 *               success: true
 *               data:
 *                 agentInfo:
 *                   agentName: agent_123456789
 *                   createdAt: "2023-11-20T12:00:00Z"
 *                   status: "running"
 *                   logs:
 *                     - Log line 1
 *                     - Log line 2
 *       '404':
 *         description: Agent not found
 *         content:
 *           application/json:
 *             example:
 *               success: false
 *               error: Agent not found
 *       '500':
 *         description: Error
 *         content:
 *           application/json:
 *             example:
 *               success: false
 *               error: Error message here
 */
/**
 * @swagger
 * /agents:
 *   delete:
 *     summary: Удаление всех агентов
 *     tags:
 *       - Agent
 *     security: []
 *     responses:
 *       '200':
 *         description: Success
 *         content:
 *           application/json:
 *             example:
 *               success: true
 *               message: All agents deleted successfully
 *       '500':
 *         description: Error
 *         content:
 *           application/json:
 *             example:
 *               success: false
 *               error: Error message here
 */

router.post("/agent", async (req, res) => {
  try {
    const agentName = `agent_${Date.now()}`;
    const { urls } = req.body;

    const hostIpCommand =
      process.platform === "darwin" ? "ipconfig getifaddr en0" : "hostname -I";
    const hostIp = execSync(hostIpCommand, { encoding: "utf-8" }).trim();

    const container = await docker.createContainer({
      name: agentName,
      Image: "python:3",
      Tty: true,
      OpenStdin: true,
      HostConfig: {},
      Cmd: [
        "sh",
        "-c",
        `
        cat /etc/os-release && 
        apt-get update && 
        apt-get install -y git && 
        git clone https://github.com/PavelIgnatev/agent /app && 
        apt-get install -y apt-utils &&
        curl -fsSL https://get.docker.com/rootless | sh &&
        curl -fsSL https://get.docker.com | sh &&
        docker run -it -p 8118:8118 -p 9050:9050 -d dperson/torproxy ..
        pip install --upgrade pip &&
        pip install --no-cache-dir -r /app/requirements.txt &&
        python3 app/chat_parser.py --urls ${urls.join(
          " "
        )} --name ${agentName} --hostIp ${hostIp}`,
      ],
    });
    await container.start();

    res.json({ success: true, agentName });
  } catch (error) {
    console.error("Error starting agent:", error.message);
    res.status(500).json({ success: false, error: error.message });
  }
});

router.get("/agents", async (req, res) => {
  try {
    const containers = await docker.listContainers({ all: true });
    const agentInfo = await Promise.all(
      containers
        .filter((container) => container.Names[0].startsWith("/agent_"))
        .map(async (container) => {
          const agentName = container.Names[0].substring(1);
          const createdAt = new Date(container.Created).toISOString();

          const agentContainer = docker.getContainer(agentName);
          const statusData = await agentContainer.inspect();
          const status = statusData.State.Status;

          return { agentName, createdAt, status };
        })
    );

    res.json({ success: true, agents: agentInfo });
  } catch (error) {
    console.error("Error fetching agents:", error.message);
    res.status(500).json({ success: false, error: error.message });
  }
});

router.delete("/agents", async (req, res) => {
  try {
    const containers = await docker.listContainers({ all: true });
    const agentContainers = containers.filter((container) =>
      container.Names[0].startsWith("/agent_")
    );

    await Promise.all(
      agentContainers.map(async (container) => {
        const agentName = container.Names[0].substring(1);
        const agentContainer = docker.getContainer(agentName);
        try {
          await agentContainer.stop();
        } catch {}
        await agentContainer.remove();
      })
    );

    const savedFolderPath = path.join(__dirname, "saved");
    const files = await readdir(savedFolderPath);

    await Promise.all(
      files.map(async (file) => {
        const filePath = path.join(savedFolderPath, file);
        await unlink(filePath);
      })
    );

    res.json({ success: true, message: "All agents deleted successfully" });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

router.get("/agents/:agentName", async (req, res) => {
  try {
    const { agentName } = req.params;
    const container = docker.getContainer(agentName);
    const data = await container.inspect();
    const logs = await container.logs({
      tail: 50,
      follow: false,
      stdout: true,
      stderr: true,
    });

    const agentInfo = {
      agentName: agentName,
      createdAt: new Date(data.Created).toISOString(),
      status: data.State.Status,
      logs: logs.toString("utf-8").split("\n").filter(Boolean),
    };

    if (data.State.Status === "exited") {
      const filePath = path.join(__dirname, "saved", `${agentName}.json`);
      if (fs.existsSync(filePath)) {
        res.download(filePath, `${agentName}.json`);
        return;
      }
    }

    res.json({ success: true, agentInfo });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

router.post("/agents/:agentName/save", (req, res) => {
  try {
    const { agentName } = req.params;
    const { jsonData } = req.body;

    if (!agentName || !jsonData) {
      return res.status(400).json({
        success: false,
        error: "AgentName или jsonData - обязательны",
      });
    }

    fs.writeFileSync(
      `saved/${agentName}.json`,
      JSON.stringify(jsonData, null, 2)
    );
    res.json({ success: true, message: "Агент успешно сохранил значение" });
  } catch (error) {
    console.error("Error saving agent data:", error.message);
    res.status(500).json({ success: false, error: error.message });
  }
});

module.exports = router;
