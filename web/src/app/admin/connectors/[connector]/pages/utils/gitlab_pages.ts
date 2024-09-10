import { PopupSpec } from "@/components/admin/connectors/Popup";
import { createConnector, runConnector } from "@/lib/connector";
import { linkCredential } from "@/lib/credential";
import { GitlabPagesConfig } from "@/lib/connectors/connectors";
import { AdvancedConfig } from "../../AddConnectorPage";

export const submitGitlabPages = async (
  selectedFiles: File[],
  base_url: any,
  setPopup: (popup: PopupSpec) => void,
  advancedConfig: AdvancedConfig,
  name?: string
) => {
  const uploadCreateAndTriggerConnector = async () => {
    const formData = new FormData();

    selectedFiles.forEach((file) => {
      formData.append("files", file);
    });

    const response = await fetch("/api/manage/admin/connector/file/upload", {
      method: "POST",
      body: formData,
    });
    const responseJson = await response.json();
    if (!response.ok) {
      setPopup({
        message: `Unable to upload files - ${responseJson.detail}`,
        type: "error",
      });
      return false;
    }

    const filePaths = responseJson.file_paths as string[];
    const [connectorErrorMsg, connector] =
      await createConnector<GitlabPagesConfig>({
        name: name ? name : `GitlabPagesConnector-${base_url}`,
        source: "gitlab_pages",
        input_type: "load_state",
        connector_specific_config: {
          base_url: base_url,
          zip_path: filePaths[0],
        },
        refresh_freq: advancedConfig.refreshFreq,
        prune_freq: advancedConfig.pruneFreq,
        indexing_start: advancedConfig.indexingStart,
      });
    if (connectorErrorMsg || !connector) {
      setPopup({
        message: `Unable to create connector - ${connectorErrorMsg}`,
        type: "error",
      });
      return false;
    }

    const credentialResponse = await linkCredential(connector.id, 0, base_url);
    if (!credentialResponse.ok) {
      const credentialResponseJson = await credentialResponse.json();
      setPopup({
        message: `Unable to link connector to credential - ${credentialResponseJson.detail}`,
        type: "error",
      });
      return false;
    }

    const runConnectorErrorMsg = await runConnector(connector.id, [0]);
    if (runConnectorErrorMsg) {
      setPopup({
        message: `Unable to run connector - ${runConnectorErrorMsg}`,
        type: "error",
      });
      return false;
    }
    setPopup({
      type: "success",
      message: "Successfully created Gitlab Pages connector!",
    });
    return true;
  };

  try {
    const response = await uploadCreateAndTriggerConnector();
    return response;
  } catch (e) {
    return false;
  }
};
