import "./styles.css";
import { mountApp } from "./app";

const root = document.querySelector<HTMLElement>("#app");
if (!root) {
  throw new Error("Missing #app root element");
}

mountApp(root);
