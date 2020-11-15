import { autoinject } from "aurelia-framework";

const DEFAULT_CLASSES = {
    "CARD": ["shadow-4", "pa1", "br2", "mb2"],
    "BUTTON-FLAT": ["pa1", "br1", "ma1", "hover-bg-near-white", "hover-shadow"],
};

@autoinject()
export class ClassesForCustomAttribute {
    constructor(private element: Element) { }

    valueChanged(newValue: string, oldValue) {
        const classList = DEFAULT_CLASSES[newValue.toUpperCase()];
        if (classList != null) {
            this.element.classList.add(...classList);
        } else {
            console.error(`Could not find classes for ${newValue} (${newValue.toUpperCase()})`);
        }
    }
}
