import { fetchSettingsSS } from "@/components/settings/lib";
import { redirect } from "next/navigation";

if (typeof Promise.withResolvers === "undefined") {
  if (typeof window !== "undefined") {
    // @ts-expect-error This does not exist outside of polyfill which this is doing
    window.Promise.withResolvers = function () {
      let resolve, reject;
      const promise = new Promise((res, rej) => {
        resolve = res;
        reject = rej;
      });
      return { promise, resolve, reject };
    };
  } else {
    // @ts-expect-error This does not exist outside of polyfill which this is doing
    global.Promise.withResolvers = function () {
      let resolve, reject;
      const promise = new Promise((res, rej) => {
        resolve = res;
        reject = rej;
      });
      return { promise, resolve, reject };
    };
  }
}

export default async function Page() {
  const settings = await fetchSettingsSS();
  if (!settings) {
    redirect("/search");
  }

  if (settings.settings.default_page === "search") {
    redirect("/search");
  } else {
    redirect("/chat");
  }
}
