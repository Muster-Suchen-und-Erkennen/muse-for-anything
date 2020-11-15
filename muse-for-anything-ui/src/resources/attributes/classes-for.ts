import { autoinject } from "aurelia-framework";

const DEFAULT_CLASSES = {
    "CARD": ["shadow-4", "pa1", "br2", "mb2"],
};

@autoinject()
export class ClassesForCustomAttribute {
    constructor(private element: Element) { }

    valueChanged(newValue: string, oldValue) {
        const classList = DEFAULT_CLASSES[newValue.toUpperCase()];
        if (classList != null) {
            this.element.classList.add(...classList);
        }
    }
}
