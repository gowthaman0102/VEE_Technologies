import asyncio
import logging
import smtplib
from email.message import EmailMessage
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.generated_report import GeneratedReport
from app.models.report_recipient import ReportRecipient


logger = logging.getLogger(__name__)


def report_email_delivery_configured() -> bool:
    has_auth_setting = bool(
        settings.report_email_smtp_username
        or settings.report_email_smtp_password
    )
    complete_auth = bool(
        settings.report_email_smtp_username
        and settings.report_email_smtp_password
    )
    return bool(
        settings.report_email_smtp_host
        and settings.report_email_from
        and (not has_auth_setting or complete_auth)
    )


async def send_report_batch_email(
    db: AsyncSession,
    *,
    company_id: int,
    records: Sequence[GeneratedReport],
) -> bool:
    if not report_email_delivery_configured():
        return False

    recipients = list(
        (
            await db.execute(
                select(ReportRecipient.email)
                .where(ReportRecipient.company_id == company_id)
                .order_by(ReportRecipient.email)
            )
        ).scalars().all()
    )
    attachments = [
        record for record in records
        if record.status == "success" and record.content and record.filename
    ]
    if not recipients or not attachments:
        return False

    message = EmailMessage()
    message["From"] = settings.report_email_from
    message["To"] = ", ".join(recipients)
    message["Subject"] = f"{len(attachments)} report files for company {company_id}"
    message.set_content("Your requested media intelligence report files are attached.")
    for record in attachments:
        content_type = record.content_type or "application/octet-stream"
        maintype, _, subtype = content_type.partition("/")
        message.add_attachment(
            record.content,
            maintype=maintype or "application",
            subtype=subtype or "octet-stream",
            filename=record.filename,
        )

    def send() -> None:
        with smtplib.SMTP(
            settings.report_email_smtp_host,
            settings.report_email_smtp_port,
            timeout=settings.report_email_timeout_seconds,
        ) as client:
            if settings.report_email_starttls:
                client.starttls()
            if settings.report_email_smtp_username and settings.report_email_smtp_password:
                client.login(
                    settings.report_email_smtp_username,
                    settings.report_email_smtp_password,
                )
            client.send_message(message)

    await asyncio.to_thread(send)
    logger.info(
        "Report batch email delivered for company %s to %s recipient(s)",
        company_id,
        len(recipients),
    )
    return True