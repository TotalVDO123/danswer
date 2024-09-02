"use client";

import * as Yup from "yup";
import { Button } from "@/components/ui/button";
import { useEffect, useState } from "react";
import { Form, Formik } from "formik";
import { SelectorFormField } from "@/components/admin/connectors/Field";
import { UserGroup } from "@/lib/types";
import { Scope } from "./types";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { useToast } from "@/hooks/use-toast";

interface CreateRateLimitModalProps {
  onSubmit: (
    target_scope: Scope,
    period_hours: number,
    token_budget: number,
    group_id: number
  ) => void;
  forSpecificScope?: Scope;
  forSpecificUserGroup?: number;
}

export const CreateRateLimitModal = ({
  onSubmit,
  forSpecificScope,
  forSpecificUserGroup,
}: CreateRateLimitModalProps) => {
  const [modalUserGroups, setModalUserGroups] = useState([]);
  const [shouldFetchUserGroups, setShouldFetchUserGroups] = useState(
    forSpecificScope === Scope.USER_GROUP
  );
  const { toast } = useToast();

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch("/api/manage/admin/user-group");
        const data = await response.json();
        const options = data.map((userGroup: UserGroup) => ({
          name: userGroup.name,
          value: userGroup.id,
        }));

        setModalUserGroups(options);
        setShouldFetchUserGroups(false);
      } catch (error) {
        toast({
          title: "Error",
          description: `Failed to fetch user groups: ${error}`,
          variant: "destructive",
        });
      }
    };

    if (shouldFetchUserGroups) {
      fetchData();
    }
  }, [shouldFetchUserGroups]);

  return (
    <div className="mt-3">
      <Dialog>
        <DialogTrigger asChild>
          <Button>Create a Token Rate Limit</Button>
        </DialogTrigger>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Create a Token Rate Limit</DialogTitle>
          </DialogHeader>
          <Formik
            initialValues={{
              enabled: true,
              period_hours: "",
              token_budget: "",
              target_scope: forSpecificScope || Scope.GLOBAL,
              user_group_id: forSpecificUserGroup,
            }}
            validationSchema={Yup.object().shape({
              period_hours: Yup.number()
                .required("Time Window is a required field")
                .min(1, "Time Window must be at least 1 hour"),
              token_budget: Yup.number()
                .required("Token Budget is a required field")
                .min(1, "Token Budget must be at least 1"),
              target_scope: Yup.string().required(
                "Target Scope is a required field"
              ),
              user_group_id: Yup.string().test(
                "user_group_id",
                "User Group is a required field",
                (value, context) => {
                  return (
                    context.parent.target_scope !== "user_group" ||
                    (context.parent.target_scope === "user_group" &&
                      value !== undefined)
                  );
                }
              ),
            })}
            onSubmit={async (values, formikHelpers) => {
              formikHelpers.setSubmitting(true);
              onSubmit(
                values.target_scope,
                Number(values.period_hours),
                Number(values.token_budget),
                Number(values.user_group_id)
              );
              return formikHelpers.setSubmitting(false);
            }}
          >
            {({ isSubmitting, values, setFieldValue }) => (
              <Form>
                {!forSpecificScope && (
                  <SelectorFormField
                    name="target_scope"
                    label="Target Scope"
                    options={[
                      { name: "Global", value: Scope.GLOBAL },
                      { name: "User", value: Scope.USER },
                      { name: "User Group", value: Scope.USER_GROUP },
                    ]}
                    includeDefault={false}
                    onSelect={(selected) => {
                      setFieldValue("target_scope", selected);
                      if (selected === Scope.USER_GROUP) {
                        setShouldFetchUserGroups(true);
                      }
                    }}
                  />
                )}
                {forSpecificUserGroup === undefined &&
                  values.target_scope === Scope.USER_GROUP && (
                    <SelectorFormField
                      name="user_group_id"
                      label="User Group"
                      options={modalUserGroups}
                      includeDefault={false}
                    />
                  )}
                <div className="flex flex-col space-y-4 pt-4">
                  <div className="flex space-y-2 flex-col">
                    <Label htmlFor="period_hours">Time Window (Hours)</Label>
                    <Input name="period_hours" type="number" />
                  </div>
                  <div className="flex space-y-2 flex-col">
                    <Label htmlFor="token_budget">
                      Token Budget (Thousands)
                    </Label>
                    <Input name="token_budget" type="number" />
                  </div>
                  <div className="flex">
                    <Button
                      type="submit"
                      disabled={isSubmitting}
                      className="mx-auto w-64"
                    >
                      Create
                    </Button>
                  </div>
                </div>
              </Form>
            )}
          </Formik>
        </DialogContent>
      </Dialog>
    </div>
  );
};
