// src/features/observer/utils/tipTreeUtils.js
import { getTipGroupKey } from "./tipUtils";

export function buildTipGroupTree(tipLogs) {
  const tree = {};

  tipLogs.forEach((log) => {
    const line = log.lineId || "UNKNOWN_LINE";
    const process = log.process || "unknown";
    const step = log.step || "unknown";
    const ppid = log.ppid || "unknown";

    // line 레벨
    if (!tree[line]) {
      tree[line] = {
        name: line,
        key: line,
        level: "line",
        children: {},
        count: 0,
      };
    }
    tree[line].count++;

    // process 레벨
    if (!tree[line].children[process]) {
      tree[line].children[process] = {
        name: process,
        key: `${line}_${process}`,
        level: "process",
        parent: line,
        children: {},
        count: 0,
      };
    }
    tree[line].children[process].count++;

    // step 레벨
    if (!tree[line].children[process].children[step]) {
      tree[line].children[process].children[step] = {
        name: step,
        key: `${line}_${process}_${step}`,
        level: "step",
        parent: `${line}_${process}`,
        children: {},
        count: 0,
      };
    }
    tree[line].children[process].children[step].count++;

    // ppid 레벨
    if (!tree[line].children[process].children[step].children[ppid]) {
      tree[line].children[process].children[step].children[ppid] = {
        name: ppid,
        key: getTipGroupKey(log), // 유틸리티 함수 사용
        level: "ppid",
        parent: `${line}_${process}_${step}`,
        count: 0,
      };
    }
    tree[line].children[process].children[step].children[ppid].count++;
  });

  return tree;
}

export function getFilteredGroups(tree, selectedNodes) {
  const groups = new Set();

  Object.values(tree).forEach((lineNode) => {
    if (selectedNodes.has(lineNode.key)) {
      Object.values(lineNode.children).forEach((processNode) => {
        Object.values(processNode.children).forEach((stepNode) => {
          Object.values(stepNode.children).forEach((ppidNode) => {
            groups.add(ppidNode.key);
          });
        });
      });
    } else {
      Object.values(lineNode.children).forEach((processNode) => {
        if (selectedNodes.has(processNode.key)) {
          Object.values(processNode.children).forEach((stepNode) => {
            Object.values(stepNode.children).forEach((ppidNode) => {
              groups.add(ppidNode.key);
            });
          });
        } else {
          Object.values(processNode.children).forEach((stepNode) => {
            if (selectedNodes.has(stepNode.key)) {
              Object.values(stepNode.children).forEach((ppidNode) => {
                groups.add(ppidNode.key);
              });
            } else {
              Object.values(stepNode.children).forEach((ppidNode) => {
                if (selectedNodes.has(ppidNode.key)) {
                  groups.add(ppidNode.key);
                }
              });
            }
          });
        }
      });
    }
  });

  return Array.from(groups);
}
