import { Github, Linkedin, Mail, Send, ArrowUpRight } from "lucide-react";
import type { Profile } from "../types";
import { safeUrl } from "../lib/format";
export function Socials({
  profile,
  icons = false,
  email = false,
}: {
  profile?: Profile;
  icons?: boolean;
  email?: boolean;
}) {
  const items = [
    { label: "GitHub", url: profile?.github_url, Icon: Github },
    { label: "Telegram", url: profile?.telegram_url, Icon: Send },
    { label: "LinkedIn", url: profile?.linkedin_url, Icon: Linkedin },
    ...(email
      ? [
          {
            label: "Email",
            url: profile?.email ? `mailto:${profile.email}` : null,
            Icon: Mail,
          },
        ]
      : []),
  ];
  return (
    <div className={`socials ${icons ? "social-icons" : ""}`}>
      {items.map(
        ({ label, url, Icon }) =>
          safeUrl(url) && (
            <a
              key={label}
              href={safeUrl(url)}
              aria-label={label}
              target="_blank"
              rel="noopener noreferrer"
            >
              {icons ? (
                <Icon size={17} strokeWidth={1.7} />
              ) : (
                <>
                  {label}
                  <ArrowUpRight size={14} />
                </>
              )}
            </a>
          ),
      )}
    </div>
  );
}
