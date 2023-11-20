const express = require("express");
const bodyParser = require("body-parser");
const swaggerJSDoc = require("swagger-jsdoc");
const swaggerUI = require("swagger-ui-express");
const agentRouter = require("./router");

const port = 7777;
const app = express();

const swaggerOptions = {
  definition: {
    openapi: "3.0.0",
    info: {
      title: "Agent Parsing API",
      version: "2.0.0",
    },
  },
  apis: ["./router.js"],
};
const swaggerSpec = swaggerJSDoc(swaggerOptions);

app.use(bodyParser.json({ limit: '1gb' }));
app.use(bodyParser.urlencoded({ limit: '1gb', extended: true }));
app.use("/", agentRouter);
app.use("/api-docs", swaggerUI.serve, swaggerUI.setup(swaggerSpec));
app.listen(port, () => {
  console.log(`Server is running on port ${port}`);
});
