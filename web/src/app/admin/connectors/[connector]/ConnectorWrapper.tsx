"use client";

import { isValidSource, ValidSources } from "@/lib/types";
import AddConnector from "./AddConnectorPage";
import { FormProvider } from "@/components/context/FormContext";
import Sidebar from "./Sidebar";
import { HeaderTitle } from "@/components/header/Header";
import { Button } from "@tremor/react";

export default function ConnectorWrapper({ connector }: { connector: string }) {
  return (
    <FormProvider>
      <div className="flex justify-center w-full h-full">
        <Sidebar />
        <div className="mt-12 w-full max-w-3xl mx-auto">
          {!isValidSource(connector) ? (
            <div className="mx-auto flex flex-col gap-y-2">
              <HeaderTitle>
                <p>&lsquo;{connector}&lsquo; is not a valid Connector Type!</p>
              </HeaderTitle>
              <Button
                onClick={() => window.open("/admin/indexing/status", "_self")}
                className="mr-auto"
              >
                {" "}
                Go home{" "}
              </Button>
            </div>
          ) : (
            <AddConnector connector={connector as ValidSources} />
          )}
        </div>
      </div>
    </FormProvider>
  );
}
