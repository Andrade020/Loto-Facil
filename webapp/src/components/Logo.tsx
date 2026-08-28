interface Props {
  onClick?: () => void;
}

/**
 * Marca Prisma: triangulo com gradiente conico combinando as cores originais
 * das tres primeiras loterias (Lotofacil/Mega-Sena/Quina) -- o "prisma"
 * separa luz em cores, aqui organiza varias loterias num so lugar.
 */
export default function Logo({ onClick }: Props) {
  const mark = (
    <>
      <span className="logo-mark">
        <span />
      </span>
      <span className="logo-word">Prisma</span>
    </>
  );
  if (onClick) {
    return (
      <button type="button" className="logo" onClick={onClick} aria-label="Prisma, ir para a página inicial">
        {mark}
      </button>
    );
  }
  return <div className="logo">{mark}</div>;
}
