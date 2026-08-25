import { defaultValueCtx, Editor, editorViewOptionsCtx, rootCtx } from "@milkdown/core";
import { clipboard } from "@milkdown/plugin-clipboard";
import { cursor } from "@milkdown/plugin-cursor";
import { emoji } from "@milkdown/plugin-emoji";
import { history } from "@milkdown/plugin-history";
import { indent } from "@milkdown/plugin-indent";
import { listener, listenerCtx } from "@milkdown/plugin-listener";
import { math } from "@milkdown/plugin-math";
import { prism } from "@milkdown/plugin-prism";
import { commonmark } from "@milkdown/preset-commonmark";
import { gfm } from "@milkdown/preset-gfm";
import { replaceAll } from "@milkdown/utils";
import { menu, menuConfigCtx } from "@milkdown-lab/plugin-menu";
import { autoinject, bindable, bindingMode, child, TaskQueue } from "aurelia-framework";
import { markdownMenuItems } from "util/markdown-menu";


@autoinject()
export class Markdown {
    @bindable editable: boolean = false;
    @bindable({ defaultBindingMode: bindingMode.toView }) markdownIn: string | null;
    @bindable({ defaultBindingMode: bindingMode.fromView }) markdownOut: string;

    @child(".markdown-container") markdownElement: HTMLDivElement;

    private queue: TaskQueue;
    private editor: Editor | null = null;

    private editorSetupDeferred = false;

    constructor(queue: TaskQueue) {
        this.queue = queue;
    }

    markdownElementChanged(newElement: HTMLDivElement) {
        if (newElement == null) {
            return;
        }

        if (this.markdownIn || this.editable) {
            // setting up the markdown editor takes some time so it is handled in an async task
            this.queue.queueTask(() => this.setupEditor(newElement));
        } else {
            this.editorSetupDeferred = true;
        }
    }

    setupEditor(newElement: HTMLDivElement) {
        Editor.make()
            .config((ctx) => {
                ctx.set(rootCtx, newElement);
                ctx.set(editorViewOptionsCtx, { editable: () => this.editable ?? false });
                ctx.set(defaultValueCtx, this.markdownIn ?? "");
                ctx.set(menuConfigCtx.key, { items: markdownMenuItems, attributes: {} });
                ctx.get(listenerCtx).markdownUpdated((ctx, markdown) => {
                    if (this.editable) {
                        this.queue.queueMicroTask(() => this.markdownOut = markdown);
                    }
                });
            })
            .use(commonmark)
            .use(gfm)
            .use(listener)
            .use(prism)
            .use(math)
            .use(clipboard)
            .use(history)
            .use(cursor)
            .use(emoji)
            .use(indent)
            .use(menu)
            .create()
            .then(editor => this.editor = editor)
            .catch(error => {
                // the editor is the only way to render the markdown, so a failed
                // setup must be visible instead of leaving an empty container
                console.error("Failed to create the markdown editor.", error);
                newElement.textContent = this.markdownIn ?? "";
            });
    }

    markdownInChanged(newMarkdown: string | null) {
        if (this.editorSetupDeferred) {
            this.editorSetupDeferred = false;
            this.queue.queueTask(() => {
                this.setupEditor(this.markdownElement);
                this.markdownInChanged(newMarkdown);
            });
        }
        this.queue.queueTask(() => {
            const markdown = newMarkdown ?? "";
            this.editor?.action(replaceAll(markdown, true));
        });
    }

    // TODO
    // editableChanged

}
