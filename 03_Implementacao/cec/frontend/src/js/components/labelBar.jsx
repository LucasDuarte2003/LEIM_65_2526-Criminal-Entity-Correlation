import React from "react";
import "../../static/css/labelBar.css";

class LabelBarPresenter {
  constructor(props) {
    this.props = props;
  }

  buildViewModel() {
    const chips = this.props.labels.map((label) => this.createChipViewModel(label));
    return {
      hasLabels: chips.length > 0,
      chips,
    };
  }

  createChipViewModel(label) {
    const isActive = this.props.labelSelecionada === label.nome;
    const typeClassName = this.getLabelTypeClassName(label.nome);

    return {
      key: label.nome,
      shortcut: label.shortcut,
      name: label.nome,
      className: `label-chip ${typeClassName} ${isActive ? "active-chip" : ""}`,
      title: `Atalho: ${label.shortcut || "-"}`,
      onClick: () => this.props.onSelecionar(isActive ? null : label.nome),
    };
  }

  getLabelTypeClassName(labelName) {
    const normalizedType = labelName.toLowerCase();
    const knownTypes = [
      "pessoa",
      "local",
      "organizacao",
      "crime",
      "data",
      "viatura",
      "matricula",
      "telemovel",
      "email",
      "cripto",
      "montante",
    ];

    return knownTypes.includes(normalizedType) ? `label-chip--${normalizedType}` : "label-chip--default";
  }
}

export default class LabelBar extends React.Component {
  constructor(props) {
    super(props);
    this.presenter = new LabelBarPresenter(props);
  }

  renderChip(chip) {
    return (
      <button key={chip.key} className={chip.className} onClick={chip.onClick} title={chip.title}>
        <span className="label-shortcut">{chip.shortcut}</span>
        <span className="label-name">{chip.name}</span>
      </button>
    );
  }

  render() {
    this.presenter = new LabelBarPresenter(this.props);
    const viewModel = this.presenter.buildViewModel();

    if (!viewModel.hasLabels) return null;

    return <div className="labels-bar">{viewModel.chips.map((chip) => this.renderChip(chip))}</div>;
  }
}
