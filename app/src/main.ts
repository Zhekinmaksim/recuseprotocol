import { createApp } from "vue";
import { createRouter, createWebHashHistory } from "vue-router";
import App from "./App.vue";
import Check from "./views/Check.vue";
import Docs from "./views/Docs.vue";
import Watchlist from "./views/Watchlist.vue";
import Verdict from "./views/Verdict.vue";
import "./styles/dry-ink.css";

const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    { path: "/", component: Check },
    { path: "/verdict/:chain/:token", component: Verdict, props: true },
    { path: "/watchlist", component: Watchlist },
    { path: "/docs", component: Docs },
  ],
});

createApp(App).use(router).mount("#app");
