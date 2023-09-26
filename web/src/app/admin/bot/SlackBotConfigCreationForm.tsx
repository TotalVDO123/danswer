import { ArrayHelpers, FieldArray, Form, Formik } from "formik";
import * as Yup from "yup";
import { PopupSpec } from "@/components/admin/connectors/Popup";
import { DocumentSet, SlackBotConfig } from "@/lib/types";
import { TextArrayField } from "@/components/admin/connectors/Field";
import { createSlackBotConfig, updateSlackBotConfig } from "./lib";

interface SetCreationPopupProps {
  onClose: () => void;
  setPopup: (popupSpec: PopupSpec | null) => void;
  documentSets: DocumentSet<any, any>[];
  existingSlackBotConfig?: SlackBotConfig;
}

export const SlackBotCreationForm = ({
  onClose,
  setPopup,
  documentSets,
  existingSlackBotConfig,
}: SetCreationPopupProps) => {
  const isUpdate = existingSlackBotConfig !== undefined;

  return (
    <div>
      <div
        className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
        onClick={onClose}
      >
        <div
          className="bg-gray-800 p-6 rounded border border-gray-700 shadow-lg relative w-1/2 text-sm"
          onClick={(event) => event.stopPropagation()}
        >
          <Formik
            initialValues={{
              channel_names: existingSlackBotConfig
                ? existingSlackBotConfig.channel_config.channel_names
                : ([] as string[]),
              document_sets: existingSlackBotConfig
                ? existingSlackBotConfig.document_sets.map(
                    (documentSet) => documentSet.id
                  )
                : ([] as number[]),
            }}
            validationSchema={Yup.object().shape({
              channel_names: Yup.array().of(Yup.string().required()),
              document_sets: Yup.array().of(Yup.number()),
            })}
            onSubmit={async (values, formikHelpers) => {
              formikHelpers.setSubmitting(true);
              let response;
              if (isUpdate) {
                response = await updateSlackBotConfig(
                  existingSlackBotConfig.id,
                  values
                );
              } else {
                response = await createSlackBotConfig(values);
              }
              formikHelpers.setSubmitting(false);
              if (response.ok) {
                setPopup({
                  message: isUpdate
                    ? "Successfully updated DanswerBot config!"
                    : "Successfully created DanswerBot config!",
                  type: "success",
                });
                onClose();
              } else {
                const errorMsg = (await response.json()).detail;
                setPopup({
                  message: isUpdate
                    ? `Error updating DanswerBot config - ${errorMsg}`
                    : `Error creating DanswerBot config - ${errorMsg}`,
                  type: "error",
                });
              }
            }}
          >
            {({ isSubmitting, values }) => (
              <Form>
                <h2 className="text-lg font-bold mb-3">
                  {isUpdate
                    ? "Update a DanswerBot Config"
                    : "Create a new DanswerBot Config"}
                </h2>
                <TextArrayField
                  name="channel_names"
                  label="Channel Names:"
                  values={values}
                  subtext="The names of the Slack channels you want DanswerBot to assist in. For example, '#ask-danswer'."
                />
                <FieldArray
                  name="document_sets"
                  render={(arrayHelpers: ArrayHelpers) => (
                    <div>
                      <div>
                        Document Sets:
                        <br />
                        <div className="text-xs">
                          The document sets that DanswerBot should search
                          through. If left blank, DanswerBot will search through
                          all documents.
                        </div>
                      </div>
                      <div className="mb-3 mt-2 flex gap-2 flex-wrap">
                        {documentSets.map((documentSet) => {
                          const ind = values.document_sets.indexOf(
                            documentSet.id
                          );
                          let isSelected = ind !== -1;
                          return (
                            <div
                              key={documentSet.id}
                              className={
                                `
                              px-3 
                              py-1
                              rounded-lg 
                              border
                              border-gray-700 
                              w-fit 
                              flex 
                              cursor-pointer ` +
                                (isSelected
                                  ? " bg-gray-600"
                                  : " hover:bg-gray-700")
                              }
                              onClick={() => {
                                if (isSelected) {
                                  arrayHelpers.remove(ind);
                                } else {
                                  arrayHelpers.push(documentSet.id);
                                }
                              }}
                            >
                              <div className="my-auto">{documentSet.name}</div>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  )}
                />
                <div className="flex">
                  <button
                    type="submit"
                    disabled={isSubmitting}
                    className={
                      "bg-slate-500 hover:bg-slate-700 text-white " +
                      "font-bold py-2 px-4 rounded focus:outline-none " +
                      "focus:shadow-outline w-full max-w-sm mx-auto"
                    }
                  >
                    {isUpdate ? "Update!" : "Create!"}
                  </button>
                </div>
              </Form>
            )}
          </Formik>
        </div>
      </div>
    </div>
  );
};
