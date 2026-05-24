import React from "react";
import "../../static/css/actionBar.css";

const SAVE_BUTTON_LABELS = Object.freeze({
  default: "Guardar",
  loading: "A guardar...",
});

class ActionBarPresenter {
  constructor(props) {
    this.props = props;
  }

  buildViewModel() {
    return {
      selectedLabelText: this.props.labelSelecionada || "nenhum",
      selectedTextText: this.props.textoSelecionado ? `"${this.props.textoSelecionado}"` : "nenhuma",
      saveButtonLabel: this.props.isLoading ? SAVE_BUTTON_LABELS.loading : SAVE_BUTTON_LABELS.default,
      isSaveDisabled: this.props.isLoading,
      isSemelhantesDisabled: !this.props.noticiaId,
      onUpdate: this.props.onUpdate,
      onRemover: this.props.onRemover,
      onGuardar: this.props.onGuardar,
      onSemelhantes: this.props.onSemelhantes,
    };
  }
}

export default class ActionBar extends React.Component {
  constructor(props) {
    super(props);
    this.presenter = new ActionBarPresenter(props);
  }

  renderInfo(viewModel) {
    return (
      <div className="action-info">
        <span>
          <strong>Tipo:</strong> {viewModel.selectedLabelText}
        </span>
        <span>
          <strong>Seleção:</strong> {viewModel.selectedTextText}
        </span>
      </div>
    );
  }

  renderButtons(viewModel) {
    return (
      <div className="action-buttons">
        <button className="btn btn-update" onClick={viewModel.onUpdate}>
          Adicionar entidade
        </button>
        <button className="btn btn-remove" onClick={viewModel.onRemover}>
          Remover entidade
        </button>
        <button className="btn btn-semelhantes" onClick={viewModel.onSemelhantes} disabled={viewModel.isSemelhantesDisabled}>
          Notícias Semelhantes
        </button>
        <button className="btn btn-save" onClick={viewModel.onGuardar} disabled={viewModel.isSaveDisabled}>
          {viewModel.saveButtonLabel}
        </button>
      </div>
    );
  }

  render() {
    this.presenter = new ActionBarPresenter(this.props);
    const viewModel = this.presenter.buildViewModel();

    return (
      <div className="action-bar">
        {this.renderInfo(viewModel)}
        {this.renderButtons(viewModel)}
      </div>
    );
  }
}