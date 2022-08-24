import { bindable } from "aurelia-framework";
import { DataItemModel } from "./ontology-graph-util/util";

export class TreeNode {
    @bindable current: DataItemModel;
}
