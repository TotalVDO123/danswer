import { Persona } from "@/app/admin/assistants/interfaces";
import { User } from "../types";
import { checkUserIsNoAuthUser } from "../user";

export function checkUserOwnsAssistant(user: User | null, assistant: Persona) {
  return checkUserIdOwnsAssistant(user?.id, assistant);
}

export function checkUserIdOwnsAssistant(
  userId: string | undefined,
  assistant: Persona
) {
  return (
    (!userId ||
      checkUserIsNoAuthUser(userId) ||
      assistant.owner?.id === userId) &&
    !assistant.is_default_persona
  );
}

export function getShownAssistants(user: User | null, assistants: Persona[]) {
  if (!user) {
    return assistants.filter((assistant) => assistant.is_default_persona);
  }

  return assistants.filter((assistant) => {
    const isVisible = user.preferences?.visible_assistants?.includes(
      assistant.id
    );
    const isNotHidden = !user.preferences?.hidden_assistants?.includes(
      assistant.id
    );
    const isSelected = user.preferences?.chosen_assistants?.includes(
      assistant.id
    );
    const isDefault = assistant.is_default_persona;
    return (isVisible && isNotHidden && isSelected) || isDefault;
  });
}

export function orderAssistantsForUser(
  assistants: Persona[],
  user: User | null
) {
  let orderedAssistants = [...assistants];

  if (user?.preferences?.chosen_assistants) {
    const chosenAssistantsSet = new Set(user.preferences.chosen_assistants);
    const assistantOrderMap = new Map(
      user.preferences.chosen_assistants.map((id: number, index: number) => [
        id,
        index,
      ])
    );

    // Sort chosen assistants based on user preferences
    orderedAssistants.sort((a, b) => {
      const orderA = assistantOrderMap.get(a.id);
      const orderB = assistantOrderMap.get(b.id);

      if (orderA !== undefined && orderB !== undefined) {
        return orderA - orderB;
      } else if (orderA !== undefined) {
        return -1;
      } else if (orderB !== undefined) {
        return 1;
      } else {
        return 0;
      }
    });

    // Filter out assistants not in the user's chosen list
    orderedAssistants = orderedAssistants.filter((assistant) =>
      chosenAssistantsSet.has(assistant.id)
    );
  }

  // Sort remaining assistants based on display_priority
  const remainingAssistants = assistants.filter(
    (assistant) => !orderedAssistants.includes(assistant)
  );
  remainingAssistants.sort((a, b) => {
    const priorityA = a.display_priority ?? Number.MAX_SAFE_INTEGER;
    const priorityB = b.display_priority ?? Number.MAX_SAFE_INTEGER;
    return priorityA - priorityB;
  });

  // Combine ordered chosen assistants with remaining assistants
  return [...orderedAssistants, ...remainingAssistants];
}
