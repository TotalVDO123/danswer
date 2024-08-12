"use client";

import { ThreeDotsLoader } from "@/components/Loading";
import { errorHandlingFetcher } from "@/lib/fetcher";
import { Text } from "@tremor/react";
import useSWR, { mutate } from "swr";
import { useState } from "react";
import {
  CloudEmbeddingProvider,
  CloudEmbeddingModel,
  AVAILABLE_CLOUD_PROVIDERS,
  AVAILABLE_MODELS,
  INVALID_OLD_MODEL,
  HostedEmbeddingModel,
  EmbeddingModelDescriptor,
} from "./components/types";
import { Connector } from "@/lib/connectors/connectors";
import OpenEmbeddingPage from "./OpenEmbeddingPage";
import CloudEmbeddingPage from "./CloudEmbeddingPage";
import { ProviderCreationModal } from "./modals/ProviderCreationModal";

import { DeleteCredentialsModal } from "./modals/DeleteCredentialsModal";
import { SelectModelModal } from "./modals/SelectModelModal";
import { ChangeCredentialsModal } from "./modals/ChangeCredentialsModal";
import { ModelSelectionConfirmationModal } from "./modals/ModelSelectionModal";
import { EMBEDDING_PROVIDERS_ADMIN_URL } from "../llm/constants";
import { AlreadyPickedModal } from "./modals/AlreadyPickedModal";

export interface EmbeddingDetails {
  api_key: string;
  custom_config: any;
  default_model_id?: number;
  name: string;
}

export function EmbeddingModelSelection({
  currentEmbeddingModel,
  updateSelectedProvider,
}: {
  currentEmbeddingModel: CloudEmbeddingModel | HostedEmbeddingModel;
  updateSelectedProvider: (
    model: CloudEmbeddingModel | HostedEmbeddingModel
  ) => void;
}) {
  const [modelTab, setModelTab] = useState<"open" | "cloud" | null>(null);

  // Cloud Provider based modals
  const [showTentativeProvider, setShowTentativeProvider] =
    useState<CloudEmbeddingProvider | null>(null);

  const [showUnconfiguredProvider, setShowUnconfiguredProvider] =
    useState<CloudEmbeddingProvider | null>(null);
  const [changeCredentialsProvider, setChangeCredentialsProvider] =
    useState<CloudEmbeddingProvider | null>(null);

  // Cloud Model based modals
  const [alreadySelectedModel, setAlreadySelectedModel] =
    useState<CloudEmbeddingModel | null>(null);
  const [showTentativeModel, setShowTentativeModel] =
    useState<CloudEmbeddingModel | null>(null);

  const [showModelInQueue, setShowModelInQueue] =
    useState<CloudEmbeddingModel | null>(null);

  // Open Model based modals
  const [showTentativeOpenProvider, setShowTentativeOpenProvider] =
    useState<HostedEmbeddingModel | null>(null);

  // Enabled / unenabled providers
  const [newEnabledProviders, setNewEnabledProviders] = useState<string[]>([]);
  const [newUnenabledProviders, setNewUnenabledProviders] = useState<string[]>(
    []
  );
  const [showDeleteCredentialsModal, setShowDeleteCredentialsModal] =
    useState<boolean>(false);
  const [showAddConnectorPopup, setShowAddConnectorPopup] =
    useState<boolean>(false);

  const { data: embeddingProviderDetails } = useSWR<EmbeddingDetails[]>(
    EMBEDDING_PROVIDERS_ADMIN_URL,
    errorHandlingFetcher
  );

  const {
    data: futureEmbeddingModel,
    isLoading: isLoadingFutureModel,
    error: futureEmeddingModelError,
  } = useSWR<CloudEmbeddingModel | HostedEmbeddingModel | null>(
    "/api/secondary-index/get-secondary-embedding-model",
    errorHandlingFetcher,
    { refreshInterval: 5000 } // 5 seconds
  );

  const { data: connectors } = useSWR<Connector<any>[]>(
    "/api/manage/connector",
    errorHandlingFetcher,
    { refreshInterval: 5000 } // 5 seconds
  );

  if (isLoadingFutureModel) {
    return <ThreeDotsLoader />;
  }

  const onConfirmSelection = async (model: EmbeddingModelDescriptor) => {
    const response = await fetch(
      "/api/search-settings/set-new-embedding-model",
      {
        method: "POST",
        body: JSON.stringify(model),
        headers: {
          "Content-Type": "application/json",
        },
      }
    );
    if (response.ok) {
      setShowTentativeModel(null);
      mutate("/api/search-settings/get-secondary-embedding-model");
      if (!connectors || !connectors.length) {
        setShowAddConnectorPopup(true);
      }
    } else {
      alert(`Failed to update embedding model - ${await response.text()}`);
    }
  };

  const currentModelName = currentEmbeddingModel?.model_name;
  const AVAILABLE_CLOUD_PROVIDERS_FLATTENED = AVAILABLE_CLOUD_PROVIDERS.flatMap(
    (provider) =>
      provider.embedding_models.map((model) => ({
        ...model,
        cloud_provider_id: provider.id,
        model_name: model.model_name, // Ensure model_name is set for consistency
      }))
  );

  const currentModel: CloudEmbeddingModel | HostedEmbeddingModel =
    AVAILABLE_MODELS.find((model) => model.model_name === currentModelName) ||
    AVAILABLE_CLOUD_PROVIDERS_FLATTENED.find(
      (model) => model.model_name === currentEmbeddingModel.model_name
    )!;
  // ||
  // fillOutEmbeddingModelDescriptor(currentEmbeddingModel);

  const onSelectOpenSource = async (model: HostedEmbeddingModel) => {
    if (currentEmbeddingModel?.model_name === INVALID_OLD_MODEL) {
      await onConfirmSelection(model);
    } else {
      setShowTentativeOpenProvider(model);
    }
  };

  const selectedModel = AVAILABLE_CLOUD_PROVIDERS[0];
  const clientsideAddProvider = (provider: CloudEmbeddingProvider) => {
    const providerName = provider.name;
    setNewEnabledProviders((newEnabledProviders) => [
      ...newEnabledProviders,
      providerName,
    ]);
    setNewUnenabledProviders((newUnenabledProviders) =>
      newUnenabledProviders.filter(
        (givenProvidername) => givenProvidername != providerName
      )
    );
  };

  const clientsideRemoveProvider = (provider: CloudEmbeddingProvider) => {
    const providerName = provider.name;
    setNewEnabledProviders((newEnabledProviders) =>
      newEnabledProviders.filter(
        (givenProvidername) => givenProvidername != providerName
      )
    );
    setNewUnenabledProviders((newUnenabledProviders) => [
      ...newUnenabledProviders,
      providerName,
    ]);
  };

  return (
    <div className="p-2">
      {alreadySelectedModel && (
        <AlreadyPickedModal
          model={alreadySelectedModel}
          onClose={() => setAlreadySelectedModel(null)}
        />
      )}

      {showTentativeOpenProvider && (
        <ModelSelectionConfirmationModal
          selectedModel={showTentativeOpenProvider}
          isCustom={
            AVAILABLE_MODELS.find(
              (model) =>
                model.model_name === showTentativeOpenProvider.model_name
            ) === undefined
          }
          onConfirm={() => {
            updateSelectedProvider(showTentativeOpenProvider);
            setShowTentativeOpenProvider(null);
          }}
          onCancel={() => setShowTentativeOpenProvider(null)}
        />
      )}

      {showTentativeProvider && (
        <ProviderCreationModal
          selectedProvider={showTentativeProvider}
          onConfirm={() => {
            setShowTentativeProvider(showUnconfiguredProvider);
            clientsideAddProvider(showTentativeProvider);
            if (showModelInQueue) {
              setShowTentativeModel(showModelInQueue);
            }
          }}
          onCancel={() => {
            setShowModelInQueue(null);
            setShowTentativeProvider(null);
          }}
        />
      )}
      {changeCredentialsProvider && (
        <ChangeCredentialsModal
          useFileUpload={changeCredentialsProvider.name == "Google"}
          onDeleted={() => {
            clientsideRemoveProvider(changeCredentialsProvider);
            setChangeCredentialsProvider(null);
          }}
          provider={changeCredentialsProvider}
          onConfirm={() => setChangeCredentialsProvider(null)}
          onCancel={() => setChangeCredentialsProvider(null)}
        />
      )}

      {showTentativeModel && (
        <SelectModelModal
          model={showTentativeModel}
          onConfirm={() => {
            setShowModelInQueue(null);
            updateSelectedProvider(showTentativeModel);
            setShowTentativeModel(null);
          }}
          onCancel={() => {
            setShowModelInQueue(null);
            setShowTentativeModel(null);
          }}
        />
      )}

      {showDeleteCredentialsModal && (
        <DeleteCredentialsModal
          modelProvider={showTentativeProvider!}
          onConfirm={() => {
            setShowDeleteCredentialsModal(false);
          }}
          onCancel={() => setShowDeleteCredentialsModal(false)}
        />
      )}

      <div className="text-sm mr-auto mb-6 divide-x-2 flex">
        <button
          onClick={() => setModelTab("cloud")}
          className={`mx-2 p-2 font-bold  ${
            modelTab == "cloud"
              ? "rounded bg-background-900 text-text-100 underline"
              : " hover:underline"
          }`}
        >
          Cloud-based
        </button>
        <div className="px-2 ">
          <button
            onClick={() => setModelTab("open")}
            className={` mx-2 p-2 font-bold  ${
              modelTab == "open"
                ? "rounded bg-background-900 text-text-100 underline"
                : "hover:underline"
            }`}
          >
            Self-hosted
          </button>
        </div>
      </div>

      {modelTab == "open" && (
        <OpenEmbeddingPage
          currentEmbeddingModel={currentEmbeddingModel}
          onSelectOpenSource={onSelectOpenSource}
          currentModelName={currentModelName!}
        />
      )}
      {modelTab == "cloud" && (
        <CloudEmbeddingPage
          setShowModelInQueue={setShowModelInQueue}
          setShowTentativeModel={setShowTentativeModel}
          currentModel={currentEmbeddingModel}
          setAlreadySelectedModel={setAlreadySelectedModel}
          embeddingProviderDetails={embeddingProviderDetails}
          newEnabledProviders={newEnabledProviders}
          newUnenabledProviders={newUnenabledProviders}
          setShowTentativeProvider={setShowTentativeProvider}
          selectedModel={selectedModel}
          setChangeCredentialsProvider={setChangeCredentialsProvider}
        />
      )}

      {!modelTab && (
        <p className="text-sm">
          Select a model type above or continue with your current embedding
          model: {currentEmbeddingModel.model_name}
        </p>
      )}
    </div>
  );
}
