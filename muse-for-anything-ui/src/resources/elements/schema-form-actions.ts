import { bindable } from "aurelia-framework";

export type UpdateSignal = () => void;
export type ActionSignal = (action: { actionType: string, key: string | number }) => void;

export class SchemaFormActions {
    @bindable key: string | number;
    @bindable actionSignal: ActionSignal;
    @bindable actions: Iterable<string>;

    removable: boolean = false;

    actionsChanged(newValue: Iterable<string>) {
        const actionSet = new Set(newValue);
        this.removable = actionSet.has("remove");
    }

    removeAction() {
        if (this.actionSignal != null) {
            this.actionSignal({ actionType: "remove", key: this.key });
        }
    }
}
