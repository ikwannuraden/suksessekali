import axios from "axios";
import bluebird from "bluebird";
import { SocksProxyAgent } from "socks-proxy-agent";
import { createClient } from "@supabase/supabase-js";
import * as fs from "fs";

const SUPABASE_URL = "https://yegmcsxgxkbqbjdmsvfm.supabase.co";
const SUPABASE_AON =
  "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InllZ21jc3hneGticWJqZG1zdmZtIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MTk2NzI3NzIsImV4cCI6MjAzNTI0ODc3Mn0.79Czw_E8h4Bm3iV22Ja6R66-l-rTHfucnuWPeWAFuAY";
const SUPABASE_TABLE_NAME = "ck_proxy";
const supabaseClient = createClient(SUPABASE_URL, SUPABASE_AON);

const waiting = (time) => {
  return new Promise((resolve) => setTimeout(resolve, time));
};

const chunk = (data, perChunk) => {
  return data.reduce((resultArray, item, index) => {
    const chunkIndex = Math.floor(index / perChunk);

    if (!resultArray[chunkIndex]) {
      resultArray[chunkIndex] = []; // start a new chunk
    }

    resultArray[chunkIndex].push(item);

    return resultArray;
  }, []);
};

const getData = (data, start, end) => {
  // const splitData = data.split(/\r?\n/).filter((n) => n);
  const sliceData = data.slice(start, end);
  return sliceData;
};

const checkProxy = async (proxy) => {
  try {
    const agent = new SocksProxyAgent(`socks5h://${proxy}`);

    // perform a GET request over the Tor SOCKS proxy
    const response = await axios.request({
      url: "https://www.alchemy.com/faucets/arbitrum-sepolia",
      method: "GET",
      httpsAgent: agent,
      httpAgent: agent,
    });

    console.log(response.data);
    console.log("Proxy Working", proxy);
    return true;
  } catch (e) {
    console.log("Proxy Bad", proxy);
    return false;
  }
};
(async () => {
  const args = process.argv;
  const startData = parseInt(args[2]);
  const endData = parseInt(args[3]);

  if (!startData && !endData) {
    console.log(`Params require "node run.js 0 5"`);
    process.exit();
  }

  const readFileProxy = fs
    .readFileSync(process.cwd() + "/proxy.csv", "utf-8")
    .split(/\r?\n/)
    .filter((n) => n);

  const proxyList = getData(readFileProxy, startData, endData);

  return bluebird.map(
    proxyList,
    async (proxy) => {
      try {
        // console.log(`Checking ${proxy}`);
        const isWorking = await checkProxy(proxy);
        if (isWorking) {
          fs.appendFileSync(process.cwd() + "/good-proxy.txt", `${proxy}\n`);
          const { error } = await supabaseClient
            .from(SUPABASE_TABLE_NAME)
            .insert({ proxy: proxy });
        }
      } catch (err) {
        console.log(err);
      }
    },
    { concurrency: 2 }
  );
})();
